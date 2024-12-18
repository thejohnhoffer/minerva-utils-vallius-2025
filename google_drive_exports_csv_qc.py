import csv
import glob
import logging
from re import match
from json import dumps
from pathlib import Path
from collections import defaultdict


logger = logging.getLogger(__name__)

class Story:

    def __init__(
        self, identifier, case, block, assay, in_path
    ):
        self.identifier = identifier
        self.in_path = in_path
        self.case = case
        self.block = block
        self.assay = assay

    def __repr__(self):
        return (
            "Story(\n"
            f"    identifier='{self.identifier}'\n"
            f"    in_path='{self.in_path}'\n"
            f"    case='{self.case}'\n"
            f"    block='{self.block}'\n"
            f"    assay='{self.assay}'\n"
            ")"
        )


class Plan:

    def __init__(
        self, name, safe_name, assay,
        marker_typos={},
        in_path_markers=None,
        in_path_groups=None,
        in_path_rois_all={}
    ):
        self.name = name
        self.safe_name = safe_name
        self.assay = assay
        self.marker_typos = marker_typos
        self.in_path_markers = in_path_markers
        self.in_path_groups = in_path_groups
        self.in_path_rois_all = in_path_rois_all


    def load_markers(self):
        if self.assay == "H&E":
            return []
        elif not self.in_path_markers:
            raise NormalizationError("missing markers")
        name_id_map = {}
        try:
            with open(self.in_path_markers, newline='', encoding='utf-8-sig') as f:
                for index,line in enumerate(csv.DictReader(f)):
                    assert "marker_name" in line.keys()
                    name_id_map[line["marker_name"]] = index
        except FileNotFoundError:
            raise NormalizationError("missing markers")
        except AssertionError:
            raise NormalizationError("invalid markers")

        return name_id_map


    def load_groups(self, parent_path, channel_markers, unfixable):
        if self.assay == "H&E":
            return []
        elif not self.in_path_groups:
            raise NormalizationError("missing groups")

        group_path = parent_path / self.in_path_groups
        group_channels = defaultdict(list)
        marker_typos = self.marker_typos
        error_message = ""
        group = ""
        try:
            with open(group_path, newline='', encoding='utf-8-sig') as f:
                for index,line in enumerate(csv.reader(f)):
                    if index == 0:
                        assert line[1] == ""
                        assert line[2] == "lower limit"
                        assert line[3] == "upper limit"
                        assert line[4] == "color"
                        continue
                    [line_group, marker_name, lower, upper, color] = line[:5]
                    if line_group not in ("", group):
                        assert all(
                            not x for x in (marker_name, lower, upper, color)
                        )
                        group = line_group
                        continue
                    if not all(
                        (marker_name, lower, upper, color)
                    ):
                        break # TODO -- handle files with empty lines
                        continue

                    group_config = {
                        "color": color,
                        "info": "",
                        "label": marker_name,
                        "min": int(lower) / 65535,
                        "max": int(upper) / 65535
                    }
                    marker_name = marker_typos.get(marker_name, marker_name)
                    marker_id = -1
                    try:
                        marker_id = channel_markers[marker_name]
                        group_channels[group].append({
                            **group_config, "id": marker_id
                        })
                    except KeyError as e:
                        unfixable["markers"].add(
                            f'{e} in [{",".join(channel_markers.keys())}]'
                            f' from "{self.in_path_markers}"'
                        )
                        error_message = "mismatch between groups and marker names"
        except AssertionError:
            raise NormalizationError("invalid groups")
        except FileNotFoundError:
            raise NormalizationError("missing groups")
        if error_message:
            raise NormalizationError(error_message)
        return [
            { "label": key, "channels": value }
            for key, value in group_channels.items()
        ]


def normalize_key(k):
    in_path = {"Path to McMicro"}
    slide = {"facility_id", "slide"}
    section = {
        "Section", "section #", "section"
    }
    identifier = {
        "case-block-section #", "case-block",
        "case-block-Section",
        "case-block-section"
    }
    if k in identifier:
        return "identifier"
    if k in section:
        return "section"
    if k in slide:
        return "slide"
    if k in in_path:
        return "in_path"
    return k


def normalize_path(v, in_root, out_root):
    known_typos = {
        (
            "lsp-analysis/cycif-production/16-Pre-Cancer-Atlas-for-Melanoma/"
            "PCAII_p16_e24/mcmicro_done/re-processed/LSP1141"
        ) : Path(
            "lsp-analysis/cycif-production/16-Pre-Cancer-Atlas-for-Melanoma/"
            "PCAII_p16_e24/mcmicro_done/re-processed/LSP11411"
        )
    }
    try:
        v = Path(v).relative_to(in_root)
        if (str(v.parent) in known_typos):
            v = known_typos[str(v.parent)] / v.name
        return Path(out_root) / v 
    except ValueError:
        pass


class NormalizationError(Exception):
    pass


class FolderAccessError(Exception):
    pass


class FileAccessError(Exception):
    pass


class AmbiguousFileError(Exception):
    pass


def normalize_value(k, v, assay):
    key = normalize_key(k)
    known_typos = {
        "MEL36 A1", "MEL36 A2", "MEL55 A2", "MEL68 A1", "MEL68 B1"
    }
    if key == "identifier":
        if v == "MEL85/MEL86-A1/A1":
            v = "MEL85_MEL86-A1_A1"
        if v in known_typos:
            v = '-'.join(v.split(' ')[0])
        if not match("^[A-Za-z0-9_-]+$", v):
            raise NormalizationError(f"Invalid '{key}'='{v}'")

    elif key == "case":
        if v in known_typos:
            v = v.split(' ')[0]
        allowed = { "MEL85/MEL86" }
        if not match("^MEL[0-9]+$", v) and v not in allowed:
            raise NormalizationError(f"Invalid '{key}'='{v}'")

    elif key == "slide":
        if v[-1] == "/":
            v = v[:-1]
        if not match("^LSP[0-9]{5}$", v):
            raise NormalizationError(f"Invalid '{key}'='{v}'")

    elif key == "in_path":
        o2_path = None
        if assay == "H&E":
            o2_path = normalize_path(
                v, "/Volumes/hms/hits/lsp/collaborations/",
                "/n/standby/hms/hits/lsp/collaborations/"
            )
        if assay == "H&E" and not o2_path:
            o2_path = normalize_path(
                v, "/Volumes/HITS/lsp-data/",
                "/n/standby/hms/hits/lsp/collaborations/"
            )
        if not o2_path:
            o2_path = normalize_path(v, "/Volumes/HiTS/", "/n/files/HiTS/")
        if not o2_path:
            o2_path = normalize_path(v, "/Volumes/HITS/", "/n/files/HiTS/")
        if not o2_path:
            raise NormalizationError(f"Unrecognized path '{v}'")

        # Fix glob patterns
        if o2_path.name == "registration.*.ome.tif":
            o2_path = o2_path.parent / "registration/*.ome.tif"

        # Check file access
        matches = glob.glob(str(o2_path))
        if not matches:
            if not o2_path.parent.is_dir():
                raise FolderAccessError(o2_path.parent)
            else:
                raise FileAccessError(o2_path)

        if len(matches) != 1:
            raise AmbiguousFileError(f"Ambiguous path '{o2_path}'")

        return matches[0]

    return v


def normalize_line(line_dict, assay, unfixable):
    try:
        return {
            normalize_key(k): normalize_value(
                k, v, assay
            )
            for k,v in line_dict.items() 
        }  
    except FolderAccessError as e:
        unfixable["folders"].add(str(e))
        unfixable["n"] += 1
    except FileAccessError as e:
        unfixable["files"].add(str(e))
        unfixable["n"] += 1
    except AmbiguousFileError as e:
        unfixable["n"] += 1
        logger.error(f'ERROR: {e}')
    except NormalizationError as e:
        unfixable["n"] += 1
        logger.error(f'ERROR: {e}')



def plan_qc(plan_path, plan, unfixable):
    assay = plan.assay

    try:
        channel_markers = plan.load_markers()
        channel_groups = plan.load_groups(
            plan_path.parent, channel_markers, unfixable
        )
        for channel_group in channel_groups:
            pass
            #print("Group", channel_group["label"], len(channel_group["channels"]))
    except NormalizationError as e:
        logger.error(f'WARNING: {e}')
        logger.warning(f'WARNING: Skipping all stories in "{plan_path}"')
        return

    with open(plan_path, newline='', encoding='utf-8-sig') as f:
        for index,line in enumerate(csv.DictReader(f)):
            normalized = normalize_line(
                line, assay, unfixable
            )
            if normalized:
                story = Story(
                    identifier=normalized["identifier"],
                    case=normalized["case"],
                    block=normalized["block"],
                    in_path=normalized["in_path"],
                    assay=assay
                )
                yield story 
            else:
                logger.warning(f'WARNING: Skipping story #{index} in "{plan_path}"')


def plan_dir_loader(plans, plan_dir, unfixable):
    yield from (
        story
        for path in plan_dir.iterdir()
        if path.is_file() and path.name in plans 
        for story in plan_qc(
            path, plans[path.name], unfixable
        )
    )


if __name__ == "__main__":
    plans = {
        "minervastories_plan_RP - TODO (H&E).csv": Plan(
            "early melanoma H&E",
            "early_melanoma_he",
            "H&E",
            in_path_rois_all={
                "H&E": Path(
                    "/n/files/HiTS/lsp-analysis/cycif-production/",
                    "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/HE_roi_coordinates"
                )
            }
        ),
        "minervastories_plan_RP - TO DO (e24).csv": Plan(
            "early melanoma cell lineage panel (e24)",
            "early_melanoma_cell_lineage_e24",
            "Cell Lineage CyCIF Panel",
            in_path_markers=Path(
                "/n/files/HiTS/lsp-analysis/cycif-production/",
                "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/p16e24_markers.csv"
            ),
            in_path_groups=Path(
                "minervastories_plan_RP - Rendering_e24.csv"
            ),
            in_path_rois_all={
                "Histopath": Path(
                    "/n/files/HiTS/lsp-analysis/cycif-production/",
                    "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/e24_histopath_coordinates"
                ),
                "GeoMx": Path(
                    "/n/files/HiTS/lsp-analysis/cycif-production/",
                    "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/e24_geomx_coordinates"
                )
            },
            marker_typos={
                "CD3e": "CD3E"
            }
        ),
        "minervastories_plan_RP - TODO (e41).csv" : Plan(
            "early melanoma tumor intrinsic (e41)",
            "early_melanoma_tumor_intrinsic_e41",
            "Tumor Intrinsic CycIF Panel",
            in_path_markers=Path(
                "/n/files/HiTS/lsp-analysis/cycif-production/",
                "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/p16_e41_markers.csv"
            ),
            in_path_groups=Path(
                "minervastories_plan_RP - Rendering_e41.csv"
            ),
            in_path_rois_all={
                "Histopath": Path(
                    "/n/files/HiTS/lsp-analysis/cycif-production/",
                    "6-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/e41_histopath_rename"
                ),
                "GeoMx": Path(
                    "/n/files/HiTS/lsp-analysis/cycif-production/",
                    "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/e41_geomx_coordinates"
                )
            },
            marker_typos={
                "KI67": "Ki67"
            }
        ),
        "minervastories_plan_RP - TODO_stageIIH&E.csv": Plan(
            "stage II p135_H&E",
            "stage_ii_p135_he",
            "H&E",
            in_path_rois_all={
                "H&E": Path(
                    "/n/files/HiTS/lsp-analysis/cycif-production/",
                    "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/p135_HE_histopath_coordinates"
                ),
            }
        ),
        "minervastories_plan_RP - TODOStageII.csv": Plan(
            "stage II tumor intrinsic (p135e9)",
            "stage_ii_tumor_intrinsic_p135e9",
            "Tumor Intrinsic CycIF Panel",
            in_path_markers=Path(
                "/n/files/HiTS/lsp-analysis/cycif-production/",
                "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/p135e9_markers.csv"
            ),
            in_path_groups=Path(
                "minervastories_plan_RP - Rendering_e9.csv"
            ),
            in_path_rois_all={
                "Histopath": Path(
                    "/n/files/HiTS/lsp-analysis/cycif-production/",
                    "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/p135_e9_histopath_coordinates"
                ),
                "GeoMx": Path(
                    "/n/files/HiTS/lsp-analysis/cycif-production/",
                    "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/p135_e9_geomx_coordinates"
                )
            },
            marker_typos={
                "CD3e": "CD3E",
                "KI67": "Ki67",
                "CD8A": "CD8a"
            }
        )
    }
    unfixable = {
        "files": set(), "folders": set(), "markers": set(),
        "n": 0
    }
    qc = list(plan_dir_loader(
        plans, Path("google_drive_exports_csv"), unfixable
    ))
    #for story in qc:
    #    print(story)

    debug_keys = [
#        "files", "folders"
        "markers"
    ]
    for debug_key in debug_keys:
        logger.warning(f'Unable to find {debug_key}:')
        for fpath in sorted(unfixable[debug_key]):
            logger.warning(f'    {fpath}')

    print(f'Using {len(qc)-unfixable["n"]}/{len(qc)}')

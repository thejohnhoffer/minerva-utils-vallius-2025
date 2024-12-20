import sys
import csv
import glob
import json
import logging
from re import match
from json import dumps
from pathlib import Path
from collections import defaultdict


logger = logging.getLogger(__name__)


class Metadata:

    def __init__(self, metadata):
        self.metadata = metadata

    def __repr__(self):
        return f'Metadata({self.title()})'

    def title(self):
        meta = self.metadata
        assay = meta["Assay Type"]
        melanoma = meta["Melanoma type"]
        case_block = meta["case-block"]
        return f'{melanoma} - {assay} - {case_block}'

    def to_mm(self, string):
        try:
            return f'{float(string):.2f}mm'
        except ValueError:
            return string

    def template(self):
        species = self.metadata["Species"]
        sex = self.metadata["Sex"]
        age = self.metadata["Age at Diagnosis"]
        diagnosis = self.metadata["Primary Diagnosis"]
        prior_melanoma = self.metadata["Prior Melanoma"]
        resection_site = self.metadata["Site of resection of Biopsy"]
        tumor_grade = self.metadata["Tumor Grade"]
        stage = self.metadata["Stage (AJCC 8th Edition)"]
        til_response = self.metadata["TIL Response"]
        invasion_depth = (
            lambda x,sep: sep.join(self.to_mm(v) for v in x.split(sep))
        )(self.metadata["depth of invasion (mm)"], ", ")
        procedure = self.metadata["procedure"]
        assay_type = self.metadata["Assay Type"]
        fixative_type = self.metadata["Fixative Type"]
        microscope = self.metadata["Microscope"]
        objective = self.metadata["Objective"]
        return f'''## Metadata  

### Demographics  
**Species:** {species}  
**Sex:** {sex}   

### Diagnosis  
**Age at Diagnosis:** {age}   
**Primary Diagnosis:** {diagnosis}  
**Prior Melanoma:** {prior_melanoma}  
**Site of Resection or Biopsy:** {resection_site}  
**Tumor Grade:** {tumor_grade}  
**Stage (AJCC 8th Edition):** {stage}  
**TIL Response:** {til_response}  
**Depth of invasion:** {invasion_depth}  
**Procedure:** {procedure}  

### Imaging  
**Assay Type:** {assay_type}  
**Fixative Type:** {fixative_type}  
**Microscope:** {microscope}  
**Objective:** {objective}   
'''


class Groups:

    def __init__(self, groups):
        self.groups = groups

    def __repr__(self):
        str_groups = ", ".join(
            f'("{group["label"]}" n={len(group["channels"])})'
            for group in self.groups
        )
        return f'Groups({str_groups})'


class Story:

    def __init__(
        self, identifier, case, block, slide,
        url_root, in_path, assay, groups, metadata
    ):
        self.identifier = identifier
        self.url_root = url_root
        self.in_path = in_path
        self.case = case
        self.block = block
        self.slide = slide
        self.assay = assay
        self.groups = groups
        self.metadata = metadata


    def out_path(self, SCRATCH, DATE, key):
        sample = self.slide
        in_path = self.in_path
        url_root = self.url_root
        identifier = self.identifier
        tif_dir = SCRATCH / DATE / key
        return Path(
            tif_dir / url_root / identifier / f"{sample}.ome.tif"
        )


    def __repr__(self):
        return (
            "Story(\n"
            f"    identifier='{self.identifier}'\n"
            f"    url_root='{self.url_root}'\n"
            f"    in_path='{self.in_path}'\n"
            f"    case='{self.case}'\n"
            f"    block='{self.block}'\n"
            f"    slide='{self.slide}'\n"
            f"    assay='{self.assay}'\n"
            f"    groups='{self.groups}'\n"
            f"    metadata='{self.metadata}'\n"
            ")"
        )


class Plan:

    metadata_path="PCAII_metadata_textfile.csv"

    def __init__(
        self, name, url_root, assay,
        marker_typos={},
        in_path_markers=None,
        in_path_groups=None,
        in_path_rois_all={},
        ignore_groups=[]
    ):
        self.name = name
        self.url_root = url_root
        self.assay = assay
        self.marker_typos = marker_typos
        self.in_path_markers = in_path_markers
        self.in_path_groups = in_path_groups
        self.in_path_rois_all = in_path_rois_all
        self.ignore_groups = ignore_groups


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
            return [{
                "label": "H&E",
                "channels": [
                    {
                        "color": "FFFFFF",
                        "min": 0,
                        "max": 1,
                        "label": "H&E",
                        "info": "",
                        "id": 0
                    }
                ],
                "render": [
                    {
                        "color": "ff0000",
                        "min": 0,
                        "max": 1,
                        "label": "Red",
                        "info": "",
                        "id": 0
                    },
                    {
                        "color": "00ff00",
                        "min": 0,
                        "max": 1,
                        "label": "Green",
                        "info": "",
                        "id": 1
                    },
                    {
                        "color": "0000ff",
                        "min": 0,
                        "max": 1,
                        "label": "Blue",
                        "info": "",
                        "id": 2
                    }
                ]
            }]
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
                        continue
                    if group in self.ignore_groups:
                        continue
                    channel_config = {
                        "color": color,
                        "info": "",
                        "label": marker_name,
                        "min": int(lower) / 65535,
                        "max": int(upper) / 65535
                    }
                    marker_name = (marker_typos or {}).get(
                        marker_name, marker_name
                    )
                    marker_id = -1
                    try:
                        marker_id = channel_markers[marker_name]
                        group_channels[group].append({
                            **channel_config, "id": marker_id
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
            { "label": key, "channels": value, "render": value }
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
            v = '-'.join(v.split(' '))
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
        elif match("^LSP[0-9]{5}$", o2_path.name):
            o2_path = o2_path / "registration/{o2_path.name}.ome.tif"

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



def validate_rois():
    roi_keys = (
        'Height', 'Id', 'Name',
        'RadiusX', 'RadiusY', 'Text', 'Width', 'X', 'Y',
        'all_points', 'all_transforms', 'type'
    ) 
    with open(roi_csv_path, newline='', encoding='utf-8-sig') as f:
        for _,line in zip([0],csv.DictReader(f)):
            if tuple(sorted(line.keys())) != roi_keys:
                assert False # TODO


def plan_qc(plan_path, plan, unfixable):
    assay = plan.assay
    url_root = plan.url_root
    parent = plan_path.parent

    try:
        channel_markers = plan.load_markers()
        groups = Groups(plan.load_groups(
            parent, channel_markers, unfixable
        ))
    except NormalizationError as e:
        logger.error(f'WARNING: {e}')
        logger.warning(f'WARNING: Skipping all stories in "{plan_path}"')
        return

    # Load metadata
    metadata_dict = {}
    try:
        metadata_path = parent / plan.metadata_path
        with open(metadata_path, newline='', encoding='utf-8-sig') as f:
            for line in csv.DictReader(f):
                identifier = normalize_value(
                    "identifier", line["case-block"], plan.assay
                )
                metadata_dict[identifier] = line
    except (FileNotFoundError, NormalizationError) as e:
        logger.error(f'WARNING: {e}')
        logger.warning(f'WARNING: Skipping all stories in "{plan_path}"')
        return
            

    # Load ROIs
    roi_path_dict = defaultdict(dict)
    roi_path_keys = [
        (roi_key, roi_path.name) for (roi_key, roi_path)
        in plan.in_path_rois_all.items()
    ]
    for roi_key, roi_path in plan.in_path_rois_all.items():
        for roi_csv_path in glob.glob(str(roi_path / "LSP*.csv")):
            slide_id = match("^LSP[0-9]{5}", Path(roi_csv_path).name)
            if not slide_id:
                logger.error(f'WARNING: Invalid LSP ID in {roi_csv_path}')
            else:
                roi_path_dict[slide_id.group()][
                    (roi_key, roi_path.name)
                ] = Path(roi_csv_path)

    with open(plan_path, newline='', encoding='utf-8-sig') as f:
        for index,line in enumerate(csv.DictReader(f)):
            normalized = normalize_line(
                line, assay, unfixable
            )
            if not normalized:
                logger.warning(f'WARNING: Skipping story #{index} in "{plan_path}"')
                continue
            slide = normalized["slide"]
            identifier = normalized["identifier"]
            metadata = metadata_dict.get(identifier)
            roi_paths = roi_path_dict[slide]
            if not metadata:
                logger.warning(f'WARNING: Skipping story #{index} in "{plan_path}"')
                unfixable["metadata"].add(f'{identifier}({assay})')
                unfixable["n"] += 1
                continue
            if len(roi_paths) != len(roi_path_keys):
                logger.warning(f'WARNING: Skipping story #{index} in "{plan_path}"')
                missing_keys = sorted(
                    roi_folder for (roi_key, roi_folder) 
                    in set(roi_path_keys) - set(roi_paths.keys())
                )
                for missing_key in missing_keys:
                    unfixable["roi_paths"].add(
                        ", ".join((plan.url_root, identifier, missing_key, slide))
                    )
                unfixable["n"] += 1
                continue
            story = Story(
                identifier=identifier,
                case=normalized["case"],
                block=normalized["block"],
                slide=slide,
                url_root=url_root,
                in_path=normalized["in_path"],
                metadata=Metadata(metadata),
                groups=groups,
                assay=assay
            )
            yield story 


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
                    "16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/e41_histopath_rename"
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
            },
            ignore_groups = [
                "Immune Activation-2"
            ]
        )
    }
    unfixable = {
        "n": 0, "metadata": set(), "roi_paths": set(),
        "files": set(), "folders": set(), "markers": set(),
    }
    qc = list(plan_dir_loader(
        plans, Path("google_drive_exports_csv"), unfixable
    ))
    unique_urls = set([
        (story.url_root, story.identifier)
        for story in qc
    ])
    assert len(unique_urls) == len(qc)

    SCRATCH = Path("/n/scratch/users/j/jth30")
    DATE="2024-12-16"

    #parser = argparse.ArgumentParser()
    #parser.add_argument("command", default="test", choices=[
    #    "test", "json", "cp_tif", "copy"
    #])
    #args = parser.parse_args()
    #command = args.command
    command = sys.argv[1] or "test"

    if command == "cp_tif":
        unique_dirs = sorted(set(
            str(story.out_path(SCRATCH, DATE, "tif").parent) for story in qc
        ))
        for dir_path in unique_dirs:
            print(f"mkdir -p {dir_path}")

    for story in qc:
        url_root = story.url_root
        identifier = story.identifier
        sample = story.slide
        if command == "json":
            json_root = Path("json") / url_root
            json_root.mkdir(parents=True, exist_ok=True)
            with open(json_root / f"{identifier}.story.json", "w") as wf:
                json_config = {
                    "masks": [], # TODO
                    "waypoints": [],
                    "groups": story.groups.groups,
                    "sample_info": {
                        "rotation": 0,
                        #"pixels_per_micron:" #TODO
                        "name": story.metadata.title(),
                        "text": story.metadata.template()
                    }
                }
                json.dump(json_config, wf)
        elif command == "cp_tif":
            in_path = story.in_path
            tif_path = story.out_path(SCRATCH, DATE, "tif")
            print(f'cp "{in_path}" "{tif_path}"')
        elif command == "masks":
            print(f'cp ')
        elif command == "copy":
            print(f'bash copy.sh "{url_root}" "{identifier}" "{sample}"')
        elif command == "transfer":
            print(f'bash transfer.sh "{url_root}" "{identifier}"')
        elif command == "cp_output":
            print(f'bash website.sh "{url_root}" "{identifier}"')

    debug_keys = [
    ]
    for debug_key in debug_keys:
        if len(unfixable[debug_key]):
            logger.warning(f'Unable to find {debug_key}:')
        for fpath in sorted(unfixable[debug_key]):
            logger.warning(f'    {fpath}')

    n_total = len(qc)+unfixable["n"] 
    if command == "test":
        print(f'Using {len(qc)}/{n_total}')
        if len(qc) == 0:
            logger.info(f'Are you on an O2 transfer node?')

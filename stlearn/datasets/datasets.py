import scanpy as sc
from .._settings import settings
from pathlib import Path
from anndata import AnnData


def example_bcba() -> AnnData:
    """\
    Download processed BCBA data (10X genomics published data).
    Reference: https://support.10xgenomics.com/spatial-gene-expression/datasets/1.1.0/V1_Breast_Cancer_Block_A_Section_1
    """
    settings.datasetdir.mkdir(exist_ok=True)
    filename = settings.datasetdir / "example_bcba.h5"
    url = "https://raw.githubusercontent.com/duypham2108/dev_st/master/tutorials/example_bcba_small.h5"
    if not filename.is_file():
        sc.readwrite._download(url=url, path=filename)
    adata = sc.read_h5ad(filename)
    return adata

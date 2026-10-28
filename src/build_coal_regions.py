"""Build an auditable coal-region dataset from a reviewed InvKG membership CSV.

Input: data/processed/districts_normalized.gpkg
       config/coal_region_membership.csv (district_code,region,legal_reference)
Outputs: data/processed/coal_districts.gpkg
         data/processed/coal_regions.gpkg
         reports/coal_region_validation.json

Do not treat a guessed district list as a legal source. Verify the membership
against the applicable version of InvKG section 2 before running.
"""
from pathlib import Path
import json
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
DISTRICTS = ROOT / 'data/processed/districts_normalized.gpkg'
MEMBERSHIP = ROOT / 'config/coal_region_membership.csv'
OUT_DIR = ROOT / 'data/processed'
REPORT_DIR = ROOT / 'reports'
REGIONS = {'Lausitzer Revier', 'Rheinisches Revier', 'Mitteldeutsches Revier'}

def main():
    if not MEMBERSHIP.exists():
        raise FileNotFoundError(
            f'Missing reviewed membership file: {MEMBERSHIP}\n'
            'Create it with columns district_code,region,legal_reference '
            'using the applicable official InvKG section 2.'
        )
    districts = gpd.read_file(DISTRICTS)
    required = {'district_code', 'district_name', 'geometry'}
    if not required.issubset(districts.columns):
        raise ValueError(f'Missing district columns: {required - set(districts.columns)}')
    districts['district_code'] = districts['district_code'].astype('string').str.strip().str.zfill(5)
    if districts['district_code'].duplicated().any():
        raise ValueError('Normalized district identifiers are not unique')
    membership = pd.read_csv(MEMBERSHIP, dtype={'district_code': 'string'}).fillna('')
    expected = {'district_code', 'region', 'legal_reference'}
    if not expected.issubset(membership.columns):
        raise ValueError(f'Missing membership columns: {expected - set(membership.columns)}')
    membership['district_code'] = membership['district_code'].str.strip().str.zfill(5)
    membership['region'] = membership['region'].str.strip()
    if membership['district_code'].duplicated().any():
        raise ValueError('Duplicate legal membership district identifiers')
    if set(membership['region']) != REGIONS:
        raise ValueError(f'Region names must be exactly: {sorted(REGIONS)}')
    if (membership['legal_reference'].str.strip() == '').any():
        raise ValueError('Every membership row needs a legal reference')
    expected_counts = {'Lausitzer Revier': 7, 'Rheinisches Revier': 7, 'Mitteldeutsches Revier': 8}
    actual_counts = membership['region'].value_counts().to_dict()
    if actual_counts != expected_counts:
        raise ValueError(f'Unexpected region counts: {actual_counts}; expected {expected_counts}')
    joined = districts.merge(membership, on='district_code', how='inner', validate='one_to_one')
    missing = sorted(set(membership['district_code']) - set(joined['district_code']))
    if missing:
        raise ValueError(f'Legal district codes missing from BKG dataset: {missing}')
    if not joined.geometry.is_valid.all() or joined.geometry.is_empty.any():
        raise ValueError('Invalid or empty district geometry')
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    district_path = OUT_DIR / 'coal_districts.gpkg'
    region_path = OUT_DIR / 'coal_regions.gpkg'
    for path in (district_path, region_path):
        if path.exists():
            path.unlink()
    joined.to_file(district_path, layer='coal_districts', driver='GPKG')
    regions = joined[['region', 'geometry']].dissolve(by='region', as_index=False)
    regions.to_file(region_path, layer='coal_regions', driver='GPKG')
    report = {'source_boundaries': str(DISTRICTS), 'legal_membership_file': str(MEMBERSHIP),
              'legal_source_url': 'https://www.gesetze-im-internet.de/invkg/__2.html',
              'input_districts': len(districts), 'matched_coal_districts': len(joined),
              'region_counts': actual_counts, 'region_polygons': len(regions),
              'crs': str(joined.crs), 'invalid_geometries': int((~joined.geometry.is_valid).sum()),
              'note': 'Membership CSV must be independently checked against the applicable legal version.'}
    (REPORT_DIR / 'coal_region_validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print('IRIS | Coal-region spatial classification completed')

if __name__ == '__main__':
    main()

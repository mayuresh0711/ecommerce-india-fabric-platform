from pathlib import Path

import pandas as pd


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_FILE = BASE_DIR / "reference-data" / "india_location_source.csv"
REGION_FILE = BASE_DIR / "reference-data" / "state_region_mapping.csv"
OUTPUT_FILE = BASE_DIR / "reference-data" / "india_locations.csv"


# ============================================================
# Step 1 — Load source data
# ============================================================

source_df = pd.read_csv(
    SOURCE_FILE,
    low_memory=False,
    dtype={"Pincode": "string"}
)

# Remove accidental index columns if present in the source file.
source_df = source_df.loc[
    :,
    ~source_df.columns.str.startswith("Unnamed:")
]


# ============================================================
# Step 2 — Normalize and validate PIN codes
# ============================================================

# PIN codes are identifiers, not numeric measures.
# Keep them as strings so leading zeroes are preserved.

source_df["Pincode"] = (
    source_df["Pincode"]
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

valid_pincode_mask = source_df["Pincode"].str.fullmatch(r"\d{6}")

print("Source rows:", len(source_df))
print("Source columns:", source_df.columns.tolist())
print("Unique PINs:", source_df["Pincode"].nunique())
print("Missing PINs:", source_df["Pincode"].isna().sum())
print("Invalid PINs:", (~valid_pincode_mask).sum())


# ============================================================
# Step 3 — Remove records with missing PINs
# ============================================================

source_df = source_df[
    source_df["Pincode"].notna()
].copy()

print(
    "Rows after removing missing PINs:",
    len(source_df)
)


# ============================================================
# Step 4 — Identify PINs with conflicting states
# ============================================================

state_profile = (
    source_df
    .groupby("Pincode")
    .agg(
        state_count=("State", "nunique")
    )
)

valid_state_pins = state_profile[
    state_profile["state_count"] == 1
].index

multi_state_pin_count = (
    state_profile["state_count"] > 1
).sum()

print(
    "PINs with multiple states:",
    multi_state_pin_count
)


# ============================================================
# Step 5 — Remove PINs with conflicting states
# ============================================================

state_clean_df = source_df[
    source_df["Pincode"].isin(valid_state_pins)
].copy()

print(
    "Unique PINs after state validation:",
    state_clean_df["Pincode"].nunique()
)


# ============================================================
# Step 6 — Identify PINs with conflicting districts
# ============================================================

district_profile = (
    state_clean_df
    .groupby("Pincode")
    .agg(
        district_count=("District", "nunique")
    )
)

valid_district_pins = district_profile[
    district_profile["district_count"] == 1
].index

multi_district_pin_count = (
    district_profile["district_count"] > 1
).sum()

print(
    "PINs with multiple districts:",
    multi_district_pin_count
)


# ============================================================
# Step 7 — Remove PINs with conflicting districts
# ============================================================

district_clean_df = state_clean_df[
    state_clean_df["Pincode"].isin(valid_district_pins)
].copy()

print(
    "Unique PINs after district validation:",
    district_clean_df["Pincode"].nunique()
)


# ============================================================
# Step 8 — Identify PINs with conflicting cities
# ============================================================

city_profile = (
    district_clean_df
    .groupby("Pincode")
    .agg(
        city_count=("City", "nunique")
    )
)

valid_city_pins = city_profile[
    city_profile["city_count"] == 1
].index

multi_city_pin_count = (
    city_profile["city_count"] > 1
).sum()

print(
    "PINs with multiple cities:",
    multi_city_pin_count
)


# ============================================================
# Step 9 — Remove PINs with conflicting cities
# ============================================================

location_clean_df = district_clean_df[
    district_clean_df["Pincode"].isin(valid_city_pins)
].copy()

print(
    "Unique PINs after city validation:",
    location_clean_df["Pincode"].nunique()
)


# ============================================================
# Step 10 — Create one row per PIN
# ============================================================

# The source contains multiple Area records for the same PIN.
# Our target locations table has one row per PIN.
#
# State, District and City have already been validated to contain
# exactly one distinct value per retained PIN.

location_master = (
    location_clean_df[
        ["Pincode", "City", "District", "State"]
    ]
    .drop_duplicates()
    .sort_values("Pincode")
    .reset_index(drop=True)
)

print(
    "Location master rows:",
    len(location_master)
)

print(
    "Unique PINs:",
    location_master["Pincode"].nunique()
)

print(
    "Duplicate PINs:",
    location_master["Pincode"].duplicated().sum()
)


# ============================================================
# Step 11 — Normalize known source state-name variants
# ============================================================

# These are known naming variations found during profiling.
# They are normalized to the canonical state names used by
# our project region mapping.

state_normalization = {
    "Chattisgarh": "Chhattisgarh",
    "Megalaya": "Meghalaya",
    "Andaman and Nico.In.": "Andaman and Nicobar Islands",
    "Pondicherry": "Puducherry",
    "Daman and Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Dadra and Nagar Hav.": "Dadra and Nagar Haveli and Daman and Diu",
}

location_master["State"] = (
    location_master["State"]
    .replace(state_normalization)
)


# ============================================================
# Step 12 — Load state-to-region mapping
# ============================================================

region_df = pd.read_csv(REGION_FILE)

print(
    "Region mapping rows:",
    len(region_df)
)

print(
    "Region mapping columns:",
    region_df.columns.tolist()
)


# ============================================================
# Step 13 — Map state to analytical region
# ============================================================

# Region is a project-defined analytical classification.
# It is not taken directly from the postal source.

location_master = location_master.merge(
    region_df,
    left_on="State",
    right_on="state",
    how="left"
)

location_master = (
    location_master
    .drop(columns=["state"])
    .rename(columns={"region": "Region"})
)


# ============================================================
# Step 14 — Validate region mapping
# ============================================================

missing_region_count = (
    location_master["Region"]
    .isna()
    .sum()
)

print(
    "Missing regions:",
    missing_region_count
)

if missing_region_count > 0:
    print("\nUnmapped states:")
    print(
        location_master[
            location_master["Region"].isna()
        ]["State"]
        .value_counts()
        .to_string()
    )

    raise ValueError(
        "Region mapping incomplete. "
        "Every retained state must have a region."
    )


# ============================================================
# Step 15 — Final location-data validation
# ============================================================

print("\n========== FINAL VALIDATION ==========")

print(
    "Rows:",
    len(location_master)
)

print(
    "Unique PINs:",
    location_master["Pincode"].nunique()
)

print(
    "Duplicate PINs:",
    location_master["Pincode"].duplicated().sum()
)

print(
    "Missing City:",
    location_master["City"].isna().sum()
)

print(
    "Missing District:",
    location_master["District"].isna().sum()
)

print(
    "Missing State:",
    location_master["State"].isna().sum()
)

print(
    "Missing Region:",
    location_master["Region"].isna().sum()
)

print("\nRegion distribution:")
print(
    location_master["Region"]
    .value_counts()
)


# ============================================================
# Step 16 — Display sample
# ============================================================

print("\nSample location records:")
print(
    location_master
    .head(10)
    .to_string(index=False)
)

# ============================================================
# Step 17 — Generate location_id
# ============================================================

# location_id is the surrogate identifier for the location master.
# IDs are generated only after all validation and cleaning steps.

location_master = (
    location_master
    .sort_values("Pincode")
    .reset_index(drop=True)
)

location_master.insert(
    0,
    "location_id",
    range(1, len(location_master) + 1)
)

# Country is fixed because this project models Indian locations.
location_master["country"] = "India"

# Arrange columns to match the source-system schema.
location_master = location_master[
    [
        "location_id",
        "Pincode",
        "City",
        "District",
        "State",
        "Region",
        "country"
    ]
]

print("\n========== LOCATION MASTER ==========")

print(
    "Rows:",
    len(location_master)
)

print(
    "Unique location IDs:",
    location_master["location_id"].nunique()
)

print(
    "Unique PINs:",
    location_master["Pincode"].nunique()
)

print("\nSample:")
print(
    location_master
    .head(10)
    .to_string(index=False)
)


# ============================================================
# Step 18 — Export cleaned location master
# ============================================================

location_master.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nLocation master exported successfully.")
print("Output file:", OUTPUT_FILE)
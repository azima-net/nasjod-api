# Import Mosques from CSV

This document explains how to use the `import_mosques_from_csv` Django management command to import mosque data from the CSV file.

## Command Usage

```bash
# Activate virtual environment
source vevn/bin/activate

# Run the import command
python nasjod/manage.py import_mosques_from_csv nasjod/static/data/mosques_with_numeric_iqama_enriched.csv

# Run in dry-run mode to test without creating objects
python nasjod/manage.py import_mosques_from_csv nasjod/static/data/mosques_with_numeric_iqama_enriched.csv --dry-run

# Skip image downloads (faster for testing)
python nasjod/manage.py import_mosques_from_csv nasjod/static/data/mosques_with_numeric_iqama_enriched.csv --skip-images
```

## CSV Column Mapping

The command maps CSV columns to Django model fields as follows:

| CSV Column | Model Field | Description |
|------------|-------------|-------------|
| `governorate` | `Address.city` | City/governorate name |
| `name_en` | `Masjid.name` | English name of the mosque |
| `name_ar` | `Masjid.name_ar` | Arabic name of the mosque |
| `phone` | `Masjid.telephone` | Phone number |
| `image1` | `Masjid.cover` | Cover image URL |
| `address_mawaqit` | `Address.additional_info` | Additional address information |
| `zipcode` | `Address.zip_code` | Postal code |
| `lat` | `Address.coordinates` | Latitude (converted to Point) |
| `lon` | `Address.coordinates` | Longitude (converted to Point) |
| `fajr_iqama` | `IqamaTime.fajr_iqama` | Fajr iqama time in minutes |
| `dhuhr_iqama` | `IqamaTime.dhuhr_iqama` | Dhuhr iqama (see special logic below) |
| `asr_iqama` | `IqamaTime.asr_iqama` | Asr iqama time in minutes |
| `maghrib_iqama` | `IqamaTime.maghrib_iqama` | Maghrib iqama time in minutes |
| `isha_iqama` | `IqamaTime.isha_iqama` | Isha iqama time in minutes |

## Special Dhuhr Iqama Logic

The `dhuhr_iqama` field has special parsing logic:

1. **Positive Integer** (e.g., `+10`, `15`): Sets `IqamaTime.dhuhr_iqama`
2. **Negative Integer** (e.g., `-10`, `-15`): Sets `IqamaTime.dhuhr_iqama_from_asr` with the absolute value
3. **Time Format** (e.g., `13:00`, `12:45`): Sets `IqamaTime.dhuhr_iqama_hour`

## Features

- **Dry Run Mode**: Use `--dry-run` to validate data without creating objects
- **Image Download & Upload**: Automatically downloads images from URLs and uploads to S3
- **Skip Images Option**: Use `--skip-images` to skip image processing for faster testing
- **Error Handling**: Continues processing even if individual rows fail
- **Transaction Safety**: Each row is processed in a database transaction
- **Duplicate Handling**: Uses `update_or_create` to handle existing records
- **Coordinate Conversion**: Automatically converts lat/lon to GeoDjango Point objects
- **Data Validation**: Validates required fields and data formats
- **Image Processing**: Validates, optimizes, and converts images to JPEG format

## Output

The command provides detailed output including:
- Success messages for created/updated records
- Error messages for failed records
- Summary statistics at the end

## Example Output

```
Row 2: Created masjid "Kasbah Mosque"
Row 2: Image uploaded for "Kasbah Mosque"
Row 3: Created masjid "Qods Mosque"
Row 3: Image uploaded for "Qods Mosque"
Row 4: Error processing "Ain Zaghouan Mosque": Invalid coordinates
...
Import completed. Created: 120, Updated: 5, Errors: 3
Images: 115 uploaded, 8 failed
```

## Notes

- The command creates `Address` objects with coordinates from lat/lon
- `IqamaTime` objects are created with today's date
- The country is automatically set to "tunisia" for all addresses
- Empty or null values are handled gracefully
- The command uses semicolon (`;`) as the CSV delimiter
- Images are downloaded, validated, optimized, and uploaded to S3
- Images are converted to JPEG format with 85% quality for optimization
- Image processing includes format validation and error handling
- Failed image downloads don't stop the mosque import process

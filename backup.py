#!/usr/bin/env python3
"""
Backup workouts.db to Google Cloud Storage.

Usage:
    python3 backup.py              # Run backup
    python3 backup.py --dry-run    # Preview without uploading

Requires:
    - google-cloud-storage
    - python-dotenv
    - .env file with GCS_BUCKET, GOOGLE_APPLICATION_CREDENTIALS

Environment variables:
    GCS_BUCKET                   - GCS bucket name
    GOOGLE_APPLICATION_CREDENTIALS - Path to service account JSON key
    BACKUP_RETAIN_DAYS           - Days to keep backups (default: 30)
"""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage

# Load .env from script directory
load_dotenv(Path(__file__).parent / ".env")

DB_PATH = Path(__file__).parent / "workouts.db"
BACKUP_PREFIX = "backups/"


def load_config():
    bucket = os.environ.get("GCS_BUCKET")
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    retain_days = int(os.environ.get("BACKUP_RETAIN_DAYS", "30"))

    if not bucket:
        raise ValueError("GCS_BUCKET not set")
    if not creds_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")
    if not Path(creds_path).exists():
        raise FileNotFoundError(f"Service account key not found: {creds_path}")

    return bucket, creds_path, retain_days


def create_backup(db_path):
    """Create a consistent SQLite backup using the backup API."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()

    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(tmp.name)

    with dst:
        src.backup(dst)

    src.close()
    dst.close()

    return tmp.name


def upload_to_gcs(client, bucket_name, local_path, blob_name):
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    size_mb = Path(local_path).stat().st_size / (1024 * 1024)
    return size_mb


def prune_old_backups(client, bucket_name, retain_days):
    bucket = client.bucket(bucket_name)
    cutoff = datetime.now(timezone.utc) - timedelta(days=retain_days)
    cutoff_ts = cutoff.timestamp()

    deleted = []
    for blob in bucket.list_blobs(prefix=BACKUP_PREFIX):
        if blob.time_created.timestamp() < cutoff_ts:
            deleted.append((blob.name, blob.time_created.strftime("%Y-%m-%d")))
            blob.delete()

    return deleted


def run_backup(dry_run=False):
    bucket_name, creds_path, retain_days = load_config()

    print(f"DB: {DB_PATH}")
    print(f"Bucket: {bucket_name}")
    print(f"Retention: {retain_days} days")

    if not DB_PATH.exists():
        print(f"✗ Database not found: {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    # Create SQLite backup
    print("Creating SQLite backup...")
    tmp_path = create_backup(DB_PATH)
    size_mb = Path(tmp_path).stat().st_size / (1024 * 1024)
    print(f"  Snapshot: {size_mb:.2f} MB")

    # Upload
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    blob_name = f"{BACKUP_PREFIX}workouts-{timestamp}.db"

    client = storage.Client.from_service_account_json(creds_path)

    if dry_run:
        print(f"  [dry-run] Would upload to: gs://{bucket_name}/{blob_name}")
        os.unlink(tmp_path)
        print("✓ Dry run complete (nothing uploaded)")
        return

    print(f"Uploading to gs://{bucket_name}/{blob_name}...")
    uploaded_mb = upload_to_gcs(client, bucket_name, tmp_path, blob_name)
    print(f"  Uploaded: {uploaded_mb:.2f} MB")

    os.unlink(tmp_path)

    # Prune old backups
    deleted = prune_old_backups(client, bucket_name, retain_days)
    if deleted:
        print(f"\nPruned {len(deleted)} old backup(s):")
        for name, date in deleted:
            print(f"  {name} ({date})")
    else:
        print(f"\nNo backups older than {retain_days} days to prune")

    print(f"\n✓ Backup complete: {blob_name}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    try:
        run_backup(dry_run=dry_run)
    except Exception as e:
        print(f"✗ Backup failed: {e}", file=sys.stderr)
        sys.exit(1)

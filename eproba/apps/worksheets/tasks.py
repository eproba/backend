import logging
from time import time

logger = logging.getLogger(__name__)


def remove_expired_deleted_worksheets():
    from .models import Worksheet

    count = 0

    for worksheet in Worksheet.objects.filter(deleted=True):
        if worksheet.updated_at.timestamp() + 2592000 < time():
            worksheet.delete()
            count += 1

    logger.info(f"Removed {count} expired deleted worksheets.")

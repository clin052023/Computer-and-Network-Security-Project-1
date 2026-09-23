from pathlib import Path


#File types allowed to be updated
allowed_file_types = {
    ".pdf",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg"
}

#100 MB max size
max_file_size = 100 * 1024 * 1024

#Check if file is allowed to be uploaded
#Return true or false with validation message
def validate_file(file_path):
    file_path = Path(file_path)

    #Check if file exists
    if not file_path.exists():
        return False, "File does not exist."

    #Check if file is actually a file
    if not file_path.is_file():
        return False, "The provided path is not a file."

    #Check file extension
    file_extension = file_path.suffix.lower()

    if file_extension not in allowed_file_types:
        return False, f"File type '{file_extension}' is not allowed."

    #Check file size
    file_size = file_path.stat().st_size

    if file_size > max_file_size:
        return False, "File is too large. Maximum file size is 100 MB."

    #File passed all checks

    return True, "File is valid."
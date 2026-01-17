import re

# Get AWS region with fallback
import boto3

REGION = boto3.session.Session().region_name or "us-west-2"


def get_aws_region() -> str:
    """Get the current AWS region."""
    return REGION


def get_ssm_parameter(name: str, with_decryption: bool = True) -> str:
    ssm = boto3.client("ssm", region_name=REGION)
    response = ssm.get_parameter(Name=name, WithDecryption=with_decryption)
    return response["Parameter"]["Value"]


def make_urls_clickable(text):
    """Convert URLs in text to clickable HTML links."""
    url_pattern = r"https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?"

    def replace_url(match):
        url = match.group(0)
        return f'<a href="{url}" target="_blank" style="color:#4fc3f7;text-decoration:underline;">{url}</a>'

    return re.sub(url_pattern, replace_url, text)


def create_safe_markdown_text(text, message_placeholder):
    """Create safe markdown text with proper encoding and newline handling"""
    # First encode/decode for safety
    safe_text = text.encode("utf-16", "surrogatepass").decode("utf-16")
    
    # Convert newlines to HTML breaks for proper rendering
    # This handles both actual newlines and any remaining escaped ones
    safe_text = safe_text.replace('\n', '<br>')
    safe_text = safe_text.replace('\\n', '<br>')
    
    message_placeholder.markdown(safe_text, unsafe_allow_html=True)
import re
import webbrowser


def make_whatsapp_link(number: str, country_code: str = "91") -> str:
    """
    Create a WhatsApp click-to-chat URL.
    Enter the number with country code, or a local number and country code.
    Example: 9876543210 -> https://wa.me/919876543210
    """
    digits = re.sub(r"\D", "", number.strip())

    if not digits:
        raise ValueError("Please enter a valid phone number.")

    # If the number starts with the selected country code, keep it.
    # Otherwise, remove a leading local trunk zero and add the country code.
    if digits.startswith(country_code) and len(digits) > len(country_code) + 7:
        international_number = digits
    else:
        digits = digits.lstrip("0")
        international_number = country_code + digits

    return f"https://wa.me/{international_number}"


if __name__ == "__main__":
    phone = input("Enter phone number: ").strip()
    country = input("Country code (default 91 for India): ").strip() or "91"

    try:
        link = make_whatsapp_link(phone, country)
        print("\nWhatsApp link:", link)
        if input("Open link in browser? (y/N): ").strip().lower() == "y":
            webbrowser.open(link)
    except ValueError as error:
        print("Error:", error)

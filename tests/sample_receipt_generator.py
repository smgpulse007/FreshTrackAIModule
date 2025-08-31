"""
Sample grocery receipt generator for testing OCR and LLM parsing.
Creates realistic receipt text samples with various formats and edge cases.
"""

sample_receipts = {
    "walmart_receipt_1": """
Walmart Supercenter
Save money. Live better.
(555) 123-4567
Manager: SARAH JOHNSON
1234 MAIN STREET
ANYTOWN TX 75001
ST# 1234 OP# 00001234 TE# 12 TR# 01234

GREAT VALUE BREAD         $1.98
BANANAS 4011              $2.45
GV WHOLE MILK 1GAL        $3.28
EGGS LARGE 12CT           $2.78
GROUND BEEF 80/20         $8.45
CHICKEN BREAST            $7.22
TOMATOES                  $1.67
ONIONS 3LB BAG           $2.45
PASTA BARILLA            $1.28
OLIVE OIL                $4.56
CHEESE SHREDDED          $3.45
YOGURT CUPS 6PK          $4.28

SUBTOTAL                 $44.05
TAX                      $2.64
TOTAL                    $46.69

DEBIT CARD              $46.69
ACCOUNT: ****1234
AUTH: 123456
REF: 789012345

01/15/24 14:23:45
Thank you for shopping!
""",

    "kroger_receipt_1": """
KROGER
1800 GROCERY LANE
HOMETOWN OH 45123
(555) 987-6543

ORGANIC SPINACH          $3.49
KROGER BREAD             $2.29
MILK 2% GALLON           $3.79
EGGS DOZEN               $2.99
SALMON FILLET            $12.99
APPLES HONEYCRISP        $4.67
CARROTS 2LB              $1.99
YOGURT GREEK             $5.49
PASTA SAUCE              $1.79
COFFEE FOLGERS           $8.99
PEANUT BUTTER            $4.29
FROZEN PIZZA             $3.99

SUBTOTAL                 $57.05
PLUS TAX                 $3.42
TOTAL                    $60.47

KROGER CARD SAVINGS      -$4.50
COUPONS                  -$2.00
FINAL TOTAL              $53.97

VISA ENDING 5678         $53.97
01/16/24 09:15:22
""",

    "target_receipt_1": """
TARGET
EXPECT MORE PAY LESS
2345 SHOPPING BLVD
CITYVILLE CA 90210
(555) 456-7890

GOOD & GATHER BREAD      $2.49
BANANAS ORGANIC          $2.89
MILK ORGANIC 1GAL        $4.99
CAGE FREE EGGS           $4.49
GROUND TURKEY            $6.79
BROCCOLI CROWNS          $2.99
SWEET POTATOES           $3.45
QUINOA                   $4.99
ALMOND BUTTER            $7.99
KOMBUCHA                 $4.49
DARK CHOCOLATE           $3.99
FROZEN BERRIES           $5.99

SUBTOTAL                 $56.54
TAX 8.75%                $4.95
TOTAL                    $61.49

TARGET CIRCLE SAVINGS    -$3.20
FINAL TOTAL              $58.29

MASTERCARD **9012        $58.29
01/17/24 16:42:11
""",

    "whole_foods_receipt": """
WHOLE FOODS MARKET
365 ORGANIC WAY
GREENTOWN WA 98765
(555) 321-0987

ORGANIC KALE             $2.99
SOURDOUGH BREAD          $4.99
ALMOND MILK              $3.49
PASTURE EGGS             $5.99
GRASS FED BEEF           $15.99
WILD SALMON              $18.99
AVOCADOS 6CT             $6.99
ORGANIC BLUEBERRIES      $4.99
COCONUT OIL              $12.99
RAW HONEY                $8.99
QUINOA PASTA             $3.99
KOMBUCHA GT'S            $4.99

SUBTOTAL                 $95.37
TAX                      $7.63
TOTAL                    $103.00

AMEX ****2468            $103.00
MEMBER SAVINGS           -$12.50
FINAL TOTAL              $90.50

01/18/24 11:30:45
Thank you for choosing Whole Foods!
""",

    "complex_receipt_errors": """
Wal▪Mart Supercenter  
Save money▪ Live better▪
(813) 932-ø562
Manager C0LLEEN BRICKEY
8885 N FL0RIDA AVE
TAMPA FL 33604
ST# 5221 OP# 00001061 TE# 06 TR# 05332

BREAD 007225003712 F         2.88 N
BREAD 007225003712 F         2.88 N  
GV PNT BUTTR 007874237003 F  3.84 N
GV PNT BUTTR 007874237003 F  3.84 N
GV PARM 1602 007874201510 F  4.98 O
GV CHNK CHKN 007874206784 F  1.98 N
GV CHNK CHKN 007874206784 F  1.98 N
12 CT NITRIL 073191913822    2.78 X
FOLGERS 002550000377 F       10.48 N
SC TWIST UP 007874222682 F   0.84 X
EGGS 060538871459 F          1.88 O

SUBTOTAL                     40.66
TAX                          1.05  
TOTAL                        41.71

DEBIT TEND                   46.30
CHANGE                       4.59

EFT DEBIT PAY FROM PRIMARY
ACCOUNT : 5259
PAYMENT DECLINED DEBIT NOT AVAILABLE
11/06/11 02:21:54

EFT DEBIT PAY FROM PRIMARY  
ACCOUNT : 6259
REF # 131000195280
NETWORK ID▪ 0071 APPR CODE 297664
11/06/11 02:22:54

Layaway is back for Electronics,
Toys, and Jewelry. 10/17/11-12/16/11
11/06/11 02:22:59
"""
}

def get_sample_receipt(receipt_name: str) -> str:
    """Get a sample receipt by name"""
    return sample_receipts.get(receipt_name, sample_receipts["walmart_receipt_1"])

def get_all_sample_receipts() -> dict:
    """Get all sample receipts"""
    return sample_receipts

def create_test_image_from_text(text: str, filename: str):
    """Create a test image from receipt text (for OCR testing)"""
    from PIL import Image, ImageDraw, ImageFont
    import textwrap
    
    # Create image
    width, height = 800, 1200
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Use default font
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Wrap and draw text
    lines = text.split('\n')
    y_position = 50
    
    for line in lines:
        if line.strip():
            draw.text((50, y_position), line, fill='black', font=font)
            y_position += 35
    
    # Save image
    image.save(filename)
    return filename

if __name__ == "__main__":
    # Create test images for each sample receipt
    import os
    test_dir = "/app/tests/sample_receipts"
    os.makedirs(test_dir, exist_ok=True)
    
    for name, text in sample_receipts.items():
        filename = os.path.join(test_dir, f"{name}.jpg")
        create_test_image_from_text(text, filename)
        print(f"Created test image: {filename}")

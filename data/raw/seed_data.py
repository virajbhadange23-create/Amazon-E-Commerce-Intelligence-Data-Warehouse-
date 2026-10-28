"""
Expanded Seed Data Generator for Amazon E-Commerce Intelligence & Data Warehouse
Generates 1,440 unique, realistic Amazon products across 12 categories & subcategories
strictly matching Kaggle Amazon dataset schema and specified price bands.
"""
import csv
import sys
import random
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

# Set fixed seed for deterministic reproducibility
random.seed(config.RANDOM_SEED)

CATEGORY_SPECS = {
    "Accessories & Cables": {
        "price_min": 199,
        "price_max": 1500,
        "brands": ["Anker", "Belkin", "UGREEN", "Spigen", "Portronics", "Ambrane", "Baseus", "TP-Link", "Amazon Basics", "Stuffcool", "ESR", "Moft"],
        "items": [
            ("USB-C to USB-C Fast Charging Nylon Braided Cable 2M (100W)", 999, 499),
            ("Magnetic Wireless Car Charger Mount with Air Vent Clip", 1499, 999),
            ("10000mAh Power Bank with 20W Fast Charging Compact Body", 1499, 999),
            ("Type-C 30W GaN Wall Adapter Dual Port Fast Charger", 1399, 799),
            ("MagSafe Snap-On Vegan Leather Wallet and Kickstand", 1299, 799),
            ("OTG Dual Drive Pen Drive USB 3.2 Gen 1 (64GB)", 1199, 599),
            ("4K 60Hz HDMI to HDMI Braided Display Cable 1.8M", 899, 399),
            ("Tempered Glass Screen Protector Pack of 2 with Alignment Tray", 899, 449),
            ("Ultra-Slim Armor Shockproof Protective Phone Bumper Case", 1299, 699),
            ("Ergonomic Memory Foam Mouse Pad with Wrist Rest", 799, 349),
            ("Multipurpose 6-in-1 Electronics Cleaning Kit with Soft Brush", 599, 249),
            ("Universal Travel Adapter with All-in-One Global Plug Converter", 1399, 799),
            ("5000mAh Ultra-Compact Pocket Power Bank Dual USB-A", 1199, 699),
            ("Multi-Port USB 3.0 Hub 4 Ports High Speed 5Gbps", 1199, 599),
            ("Adjustable Aluminum Desktop Cell Phone and Tablet Stand", 899, 449),
            ("Clip-On Ring Light for Video Conference and Streaming", 999, 499),
            ("Self-Adhesive Silicone Cable Organizer Clips Pack of 6", 399, 199),
            ("Anti-Lost Bluetooth Smart Tracker Tag Key Finder", 1499, 899),
            ("Waterproof Portable Travel Cable Organizer Pouch", 799, 399),
            ("Fast Wireless Charging Pad 15W Qi-Certified with LED Indicator", 1399, 749)
        ]
    },
    "Audio & Headphones": {
        "price_min": 799,
        "price_max": 8000,
        "brands": ["Sony", "boAt", "JBL", "Sennheiser", "OnePlus", "Realme", "Anker Soundcore", "Noise", "Boult", "Skullcandy", "Portronics"],
        "items": [
            ("Active Noise Cancelling Wireless Over-Ear Headphones 50H", 7499, 4999),
            ("True Wireless in-Ear Earbuds with 40H Playtime and Fast Charge", 3490, 1499),
            ("Wireless Neckband Bluetooth Earphones with Magnetic Earbuds", 2499, 1199),
            ("IPX7 Waterproof Portable Bluetooth Speaker with Deep Bass", 5999, 3499),
            ("Entry Level Studio Monitor Over-Ear Wired Headphones", 4990, 3290),
            ("Compact Pocket Bluetooth Speaker with 16H Battery", 2999, 1499),
            ("Gaming Headset with Retractable Noise Cancelling Microphone", 4999, 2699),
            ("Spatial Audio Wireless Earbuds with Touch Sensor Controls", 6999, 4299),
            ("True Wireless Sports Earbuds with Secure Ear Hooks IPX7", 4499, 2199),
            ("Dual Driver Bluetooth Neckband with Environmental Noise Cancellation", 2999, 1499),
            ("Hi-Res Audio Certified Wired in-Ear Monitors IEM", 3499, 1899),
            ("Open-Ear Air Conduction Wireless Sports Headphones", 5999, 3499),
            ("Hybrid Dual ANC Wireless Earbuds with Wireless Charging Case", 6999, 4499),
            ("Studio Podcast Cardioid USB Vocal Microphone", 6499, 3999),
            ("Wireless Neckband Earphones with 30H Playtime Fast Charge", 1999, 999),
            ("Deep Bass On-Ear Wired Headphones with In-Line Mic", 1499, 799),
            ("Portable Clip-On Bluetooth Speaker Waterproof IPX5", 1899, 1099),
            ("Bass Boosted Wireless Earphones with Magnetic Hall Switch", 2299, 1199),
            ("True Wireless Gaming Earbuds 45ms Ultra Low Latency", 3499, 1799),
            ("Compact TV Soundbar 40W with Bluetooth 5.3 and Aux In", 5999, 3499)
        ]
    },
    "Home & Kitchen Appliances": {
        "price_min": 1500,
        "price_max": 20000,
        "brands": ["Philips", "Prestige", "Morphy Richards", "Havells", "Kent", "Pigeon", "Eureka Forbes", "Atomberg", "Wonderchef", "Milton", "Bajaj", "Crompton"],
        "items": [
            ("Digital Convection Air Fryer 4.2L Rapid Air Technology", 11995, 6999),
            ("750W Heavy Duty Mixer Grinder with 4 Stainless Steel Jars", 6295, 2999),
            ("Smart RO+UV+UF Alkaline Mineral Water Purifier 8L", 18999, 12499),
            ("1200mm BLDC Smart Ceiling Fan with Remote Control", 5490, 3490),
            ("Smart Electric Pressure Cooker 7-in-1 Multi-Cooker 6L", 12999, 7999),
            ("15-Bar Pump Espresso and Cappuccino Maker Machine", 14999, 8999),
            ("Induction Cooktop 2000W with Feather Touch Controls", 4295, 2199),
            ("Smart Robotic Vacuum Cleaner with Laser Navigation and Mop", 19999, 14999),
            ("Nutri-Blend Compact Smoothie Maker and Blender 400W", 4999, 2499),
            ("Instant 3L Water Heater Geyser 3000W Copper Heating Element", 5990, 3299),
            ("Double Wall Vacuum Insulated Stainless Steel Flask 1.5L", 1895, 1199),
            ("23L Convection Microwave Oven with Auto Cook Menus", 15990, 10990),
            ("Handheld Garment Clothes Steamer 1200W Fast Heat-up", 3999, 1999),
            ("Electric Cordless Glass Kettle 1.8L with Blue LED Light", 2499, 1199),
            ("Stainless Steel 3-Piece Triply Cookware Set with Glass Lids", 6499, 3499),
            ("Cold Press Slow Juicer 200W for Maximum Nutrient Extraction", 15999, 9999),
            ("Non-Stick 4-Piece Kitchen Cookware Set Hard Anodized", 5999, 2899),
            ("Smart Room True HEPA Air Purifier CADR 250m3/h", 16990, 9990),
            ("Electric Food Chopper and Vegetable Processor 300W", 2499, 1299),
            ("Sandwich and Panini Maker 1000W Non-Stick Grill Plates", 2999, 1699)
        ]
    },
    "Smartphones & Mobile": {
        "price_min": 8000,
        "price_max": 80000,
        "brands": ["Samsung Galaxy", "Apple iPhone", "OnePlus", "Xiaomi Redmi", "Realme", "Google Pixel", "Vivo", "iQOO", "Motorola", "Poco"],
        "items": [
            ("5G Smartphone with 120Hz Curved AMOLED 8GB RAM 128GB Storage", 28999, 21999),
            ("AI Flagship Smartphone Periscope Telephoto Camera 12GB 256GB", 74999, 59999),
            ("Superfast 67W Charging 5G Smartphone 5000mAh Battery", 22999, 16499),
            ("Ultra-Slim 5G Smartphone with Optical Image Stabilization OIS", 32999, 24999),
            ("Gaming Flagship 5G Phone Snapdragon 8 Gen Processor 16GB RAM", 54999, 44999),
            ("Budget Performance 5G Smartphone 6000mAh Massive Battery", 14999, 10999),
            ("Compact Pocket 5G Smartphone with Clean Android Experience", 44999, 34999),
            ("Portrait Camera Specialist 5G Smartphone with Ring Aura Light", 36999, 28999),
            ("All-Rounder 5G Smartphone with 108MP Pro-Grade Camera", 25999, 18999),
            ("Affordable 5G Smartphone with 90Hz Display and Stereo Speakers", 12999, 9499),
            ("High Performance Flagship 5G Phone 144Hz AMOLED Display", 49999, 39999),
            ("Ultra-Tough Drop-Resistant Curved Display 5G Smartphone", 29999, 22999),
            ("Flagship AI Smartphone Dual Display Quad Camera 16GB", 78999, 64999),
            ("Creator Edition 5G Phone with 4K 60fps Selfie Camera", 38999, 29999),
            ("Lightweight Sleek 5G Phone 7.8mm Thickness Gorilla Glass", 24999, 17999),
            ("Waterproof IP68 Flagship 5G Smartphone Wireless Charging", 69999, 54999),
            ("Everyday Reliable 5G Phone 4 Years Android Updates 128GB", 18999, 13999),
            ("Turbo Fast Gaming 5G Phone with Liquid Vapor Chamber Cooling", 33999, 26999),
            ("Cinematic 4K Video 5G Smartphone with Dedicated Sound Chip", 42999, 32999),
            ("Long-Life Battery 5G Smartphone with Reverse Wired Charging", 16999, 11999)
        ]
    },
    "Laptops & Computers": {
        "price_min": 25000,
        "price_max": 150000,
        "brands": ["Apple MacBook", "Dell XPS", "HP Pavilion", "Lenovo ThinkPad", "ASUS ROG", "Acer Swift", "MSI Modern", "Lenovo IdeaPad", "HP Omen", "ASUS ZenBook"],
        "items": [
            ("Thin & Light Laptop 15.6-inch FHD Intel Core i5 16GB 512GB SSD", 69990, 48990),
            ("Gaming Laptop AMD Ryzen 7 16GB RTX 4060 144Hz IPS 1TB SSD", 119990, 89990),
            ("Ultra-Portable Laptop 13.3-inch Retina Display 8-Core 256GB SSD", 99900, 79990),
            ("Performance Laptop 14-inch OLED Display Intel Core i7 16GB 1TB", 94990, 74990),
            ("Business Laptop 14-inch Anti-Glare Intel Core i5 16GB 512GB SSD", 78990, 56990),
            ("Affordable Student Laptop 15.6-inch Intel Core i3 8GB 512GB SSD", 45990, 31990),
            ("Flagship Thin & Light Laptop 16-inch 3.2K 120Hz OLED Core Ultra 7", 149990, 119990),
            ("Pro Gaming Laptop Intel Core i7 32GB RTX 4070 240Hz QHD Display", 149990, 119990),
            ("Convertible 2-in-1 Touchscreen Laptop with Active Stylus Pen", 84990, 62990),
            ("Creator Laptop 15.6-inch 100% DCI-P3 Color Accurate Intel i7 1TB", 109990, 84990),
            ("Slim Metal Body Ultrabook 14-inch Ryzen 5 16GB 512GB Backlit Keys", 58990, 41990),
            ("Heavy-Duty Workstation Laptop Intel Core i7 32GB 1TB SSD Quadro", 145990, 119990),
            ("Entry Level Laptop 14-inch Celeron 8GB RAM 256GB SSD Windows 11", 34990, 24990),
            ("Dual Screen OLED Laptop 14-inch Touchscreen Core Ultra 9 32GB", 149990, 124990),
            ("Lightweight 1.1kg Magnesium Alloy Laptop 14-inch Core i5 16GB", 82990, 59990),
            ("High Frame Rate Esports Laptop 15.6-inch 165Hz Ryzen 7 RTX 4050", 98990, 76990),
            ("Everyday Office Laptop 15.6-inch Ryzen 5 8GB 512GB Anti-Glare", 52990, 37990),
            ("Premium CNC Aluminum Ultrabook 13.4-inch 4K Touch 16GB 512GB", 139990, 112990),
            ("All-Day Battery Laptop 15-inch M-Series Processor 16GB 512GB SSD", 134900, 114900),
            ("Silent Fanless Lightweight Laptop 13.6-inch Liquid Retina Display", 114900, 92990)
        ]
    },
    "Smart Home & IoT": {
        "price_min": 599,
        "price_max": 25000,
        "brands": ["Amazon Echo", "Google Nest", "TP-Link Tapo", "Philips Hue", "Wipro", "Qubo", "Syska", "Yale", "Ring", "Aqara", "Oakter", "EZVIZ"],
        "items": [
            ("Smart Wi-Fi Indoor Pan Tilt Security Camera 2K 3MP Two-Way Audio", 3999, 2199),
            ("Smart Speaker with Deep Bass & Alexa Voice Control (5th Gen)", 5499, 3999),
            ("16A Smart Wi-Fi Plug with Real-Time Energy Monitoring", 2290, 899),
            ("Smart Wi-Fi Multicolor LED Bulb 16 Million Colors Alexa Compatible", 1299, 499),
            ("Smart Digital Door Lock with Biometric Fingerprint & Passcode", 24990, 13990),
            ("Wi-Fi Smart Video Doorbell with 1080p HD Video & Night Vision", 11999, 6999),
            ("Smart Universal Remote IR Blaster for TV and AC via Mobile App", 2499, 1199),
            ("Smart 5-Meter Multicolor RGB Wi-Fi LED Light Strip Music Sync", 3499, 1899),
            ("Smart Air Quality Monitor Sensor with Temperature & Humidity", 4999, 2999),
            ("Smart Curtain Robot Electric Automatic Motor Controller", 9999, 6499),
            ("Outdoor Weatherproof Security Camera with Spotlight & Siren 2K", 6999, 3999),
            ("Smart Motion Sensor Wireless Zigbee Battery Operated", 2499, 1499),
            ("Smart Water Leak Sensor Detector with App Notification Alert", 2999, 1699),
            ("Smart Window and Door Contact Sensor Pack of 2 Wireless", 2799, 1499),
            ("Smart Radiator Thermostat Valve Wi-Fi Room Heating Controller", 8999, 5499),
            ("Smart Ceiling Downlight 10W Tunable White and Color Ambiance", 1999, 999),
            ("Touch Smart Light Switch Board 4-Gang Wi-Fi Glass Panel", 4999, 2799),
            ("Smart Automatic Pet Feeder with HD Camera & Scheduled Dispenser", 12999, 7999),
            ("Smart Wi-Fi Sprinkler Controller 8-Zone Automated Watering", 14999, 8999),
            ("Smart Keyless Bluetooth Padlock with Fingerprint Unlock", 3999, 1999)
        ]
    },
    "Wearable Technology": {
        "price_min": 1299,
        "price_max": 45000,
        "brands": ["Apple Watch", "Samsung Galaxy Watch", "Noise", "Fire-Boltt", "boAt", "Amazfit", "Fitbit", "Fastrack", "Garmin", "Titan", "OnePlus", "WHOOP"],
        "items": [
            ("Smartwatch with 1.96-inch AMOLED Display & Bluetooth Calling", 7999, 2499),
            ("GPS Running Multisport Smartwatch with AMOLED Touchscreen", 44990, 36990),
            ("Advanced Health Smartwatch with ECG Heart Rate & Body Composition", 36999, 22999),
            ("Fitness Tracker Band with Continuous SpO2 & Sleep Tracking", 4999, 2499),
            ("Rugged Outdoor Smartwatch 14-Day Battery Life Dual-Band GPS", 19999, 12999),
            ("Luxury Stainless Steel Mesh Strap Smartwatch 1.43-inch AMOLED", 11995, 4995),
            ("Bluetooth Calling Smartwatch with AI Voice Assistant 1.85-inch", 5999, 1499),
            ("Smart Ring Health Tracker with Titanium Finish & Sleep Metrics", 24999, 16999),
            ("Kids Safety GPS Smartwatch with Voice Calling & SOS Button", 6999, 3499),
            ("Ultra-Slim Fitness Smartwatch 100+ Sports Modes 5ATM Waterproof", 8999, 3999),
            ("Smartwatch with Dual Engine Architecture Wear OS by Google", 27999, 21999),
            ("Classic Analog-Digital Hybrid Smartwatch 30-Day Battery", 14995, 8995),
            ("Golf GPS Smartwatch with Preloaded 42000 Worldwide Courses", 34990, 26990),
            ("Diving Smartwatch 100M Water Resistant with Sapphire Crystal", 44990, 35990),
            ("Aviation Aviator GPS Smartwatch with Moving Map & Weather", 44990, 37990),
            ("Fitness Watch with Built-in Compass Altimeter Barometer Sensors", 16999, 10999),
            ("Fashion Metallic Strap Smartwatch with Diamond Cut Bezel", 9995, 3495),
            ("Ultra Battery Life Smartwatch 24-Day Endurance Dual Display", 18999, 11999),
            ("Smartwatch with NFC Contactless Payments & Offline Music Storage", 22999, 15999),
            ("Swim-Proof Smartwatch with Stroke Detection & SWOLF Metric", 12999, 6999)
        ]
    },
    "Gaming & Consoles": {
        "price_min": 1800,
        "price_max": 55000,
        "brands": ["Sony PlayStation", "Microsoft Xbox", "Nintendo", "Razer", "Logitech G", "SteelSeries", "HyperX", "Corsair", "Redragon", "Thrustmaster", "ASUS ROG"],
        "items": [
            ("Wireless Controller for Console with Haptic Feedback & Triggers", 5990, 4690),
            ("Gaming Console Slim 1TB High-Speed SSD 4K 120Hz Output", 54990, 47990),
            ("Handheld Gaming Console 7-inch 120Hz Display 512GB Storage", 54990, 44990),
            ("Mechanical RGB Gaming Keyboard Hot-Swappable Linear Switches", 12999, 7499),
            ("Ultra-Lightweight Wireless Gaming Mouse 30000 DPI Optical Sensor", 14999, 9499),
            ("7.1 Virtual Surround Sound Multiplatform Gaming Headset", 8990, 4990),
            ("Racing Steering Wheel and Floor Pedals Dual-Motor Force Feedback", 39995, 27990),
            ("Customizable 15 LCD Keys Stream Deck for Live Streaming", 15999, 11499),
            ("RGB Extended Gaming Mouse Pad Desk Mat 900x400mm", 1999, 899),
            ("Internal M.2 NVMe Gen4 SSD 2TB with Dedicated Aluminum Heatsink", 19999, 13999),
            ("Virtual Reality Mixed Reality Standalone 128GB Headset", 54990, 44990),
            ("Ergonomic Flight Simulator Joystick and Throttle System HOTAS", 18999, 12999),
            ("Low Profile Wireless Mechanical Gaming Keyboard LightSync RGB", 19995, 14995),
            ("Gaming Earbuds with Ultra-Low Latency 2.4GHz Wireless Dongle", 9999, 5999),
            ("Xbox Wireless Bluetooth Controller with Textured Grip", 5990, 4490),
            ("Adjustable Gaming Microphone with Tap-to-Mute & RGB Shock Mount", 11999, 6999),
            ("Dual Fast Charging Dock Station for Console Controllers", 2999, 1499),
            ("Optical Gaming Mouse with 8 Programmable Buttons 16000 DPI", 3999, 1899),
            ("Compact 60% Mechanical Gaming Keyboard RGB Backlit", 4999, 2499),
            ("External Game Drive 2TB USB 3.2 Gen 1 Portable Hard Drive", 8999, 5499)
        ]
    },
    "Office Products & Stationery": {
        "price_min": 350,
        "price_max": 25000,
        "brands": ["Green Soul", "Logitech", "Epson", "Casio", "Fellowes", "Scotch", "Kangaroo", "Samsonite", "Parker", "Classmate", "Pidilite", "Amazon Basics"],
        "items": [
            ("Ergonomic High-Back Executive Office Chair with Lumbar Support", 22990, 14990),
            ("All-in-One Multi-Function Wi-Fi Ink Tank Color Printer", 17999, 13499),
            ("Silent Wireless Keyboard and Optical Mouse Combo 2.4GHz", 2995, 1795),
            ("Advanced Scientific Non-Programmable Calculator 552 Functions", 1695, 1295),
            ("Cross-Cut 8-Sheet Paper and Credit Card Shredder for Home Office", 8999, 5499),
            ("Premium Ballistic Nylon 15.6-inch Business Laptop Backpack", 6990, 4190),
            ("Luxury Stainless Steel Trim Rollerball Pen Fine Nib Luxury Box", 850, 499),
            ("Thermal Laminating Machine Compact Warm-up for A4 Documents", 3499, 2199),
            ("Adjustable Heavy Duty Metal Dual Monitor Desk Mount Arm", 5999, 3299),
            ("Wooden Multipurpose Desk Organizer with Pen Stand & Drawer", 1199, 599),
            ("Heavy-Duty All-Metal Plier Stapler 50-Sheet Capacity", 650, 399),
            ("Self-Healing Rotary Cutting Mat A3 Double-Sided Grid", 999, 499),
            ("Pack of 5 Spiral Bound Subject Notebooks 300 Pages Rule Ruled", 750, 450),
            ("Ergonomic Under Desk Footrest Cushion with Non-Slip Bottom", 2199, 1199),
            ("Rechargeable AA Batteries High Capacity 2500mAh Pack of 4", 1499, 999),
            ("Document Safe Box with Electronic Keypad Lock 16L Capacity", 7999, 4999),
            ("LED Architect Desk Lamp with Clamp and 5 Color Temperature Modes", 3999, 2199),
            ("Electric Pencil Sharpener Heavy Duty for Classroom & Office", 1999, 999),
            ("Dry Erase Magnetic Whiteboard 3x2 Feet with Aluminum Frame", 2499, 1299),
            ("Compact Comb Binding Machine 120-Sheet Capacity", 6999, 4299)
        ]
    },
    "Cameras & Photography": {
        "price_min": 1200,
        "price_max": 95000,
        "brands": ["Canon", "Sony Alpha", "Nikon", "GoPro", "DJI", "Boya", "Godox", "Joby", "Tamron", "Sigma", "Digitek", "Vanguard"],
        "items": [
            ("24.2 MP Mirrorless Digital Camera with 18-45mm IS STM Lens Kit", 65995, 52990),
            ("Waterproof Action Camera 5.3K 60fps Video with Dual LCD Screens", 44990, 34990),
            ("Ultralight Foldable Drone with 4K HDR Camera 3-Axis Gimbal", 64990, 49990),
            ("Wireless Lavalier Microphone System with 2 Transmitters & Case", 14999, 8999),
            ("Professional Aluminum Heavy Duty Tripod with Fluid Pan Head", 7999, 4299),
            ("50mm f/1.8 Prime Portrait Lens for Full Frame Mirrorless", 18990, 13490),
            ("RGB LED Video Light Panel Built-in 4000mAh Battery for Vlogging", 4999, 2499),
            ("Flexible GorillaPod Tripod with Magnetic Feet for Smartphone/DSLR", 3499, 1999),
            ("Camera Backpack Bag Waterproof with Padded Modular Dividers", 5999, 3299),
            ("Portable Electronic Gimbal Stabilizer for Smartphone 3-Axis", 11999, 7499),
            ("Speedlite On-Camera Flash with High Speed Sync 1/8000s", 8999, 5499),
            ("Circular Polarizing CPL Lens Filter 67mm Multi-Coated", 2499, 1199),
            ("Variable ND Neutral Density Filter ND2-ND400 77mm Slim Frame", 3499, 1899),
            ("Studio Continuous Softbox Lighting Kit with 85W Bulbs Pair", 6999, 3999),
            ("MicroSDXC 128GB V30 4K UHD Memory Card 190MB/s Read", 2499, 1199),
            ("High Speed CFexpress Type B Card 128GB 1700MB/s Read", 14999, 9999),
            ("Camera Cleaning Kit with Sensor Swab Blower Lens Pen", 1499, 699),
            ("Dual Battery Charger with 2 Replacement Rechargeable Batteries", 3499, 1899),
            ("Heavy Duty Professional Light Stand 9 Feet Spring Cushioned", 2999, 1499),
            ("Motorized Camera Slider for Cinematic Time-Lapse & Video", 19999, 12999)
        ]
    },
    "Television & Home Entertainment": {
        "price_min": 12000,
        "price_max": 120000,
        "brands": ["Samsung", "Sony Bravia", "LG", "TCL", "Xiaomi", "Hisense", "Acer", "Vu", "Philips", "Toshiba"],
        "items": [
            ("55-inch Crystal 4K UHD Smart LED TV with HDR10+ and Alexa", 64900, 41990),
            ("43-inch 4K Ultra HD Smart Google LED TV with Dolby Vision Atmos", 42990, 27990),
            ("65-inch 4K Smart OLED Cinema Television 120Hz Refresh Rate", 119990, 94990),
            ("32-inch HD Ready Smart Android TV with Bezel-Less Display", 18990, 10990),
            ("50-inch 4K Ultra HD QLED Smart TV Quantum Dot Color", 54990, 36990),
            ("75-inch 4K Ultra HD Smart LED Google TV with Direct Full Array", 119900, 89990),
            ("Home Theater Projector Full HD 1080p 4K Supported 8000 Lumens", 24999, 14999),
            ("Ultra Short Throw 4K Laser Cinema TV Projector 2500 ANSI", 119990, 94990),
            ("Motorized Drop-Down Projector Screen 100-inch 16:9 HD", 14999, 8999),
            ("Universal Full Motion Heavy Duty TV Wall Mount Bracket 32-75 inch", 3999, 1899),
            ("Streaming Media Player 4K Ultra HD with Wi-Fi 6 & Voice Remote", 6499, 4499),
            ("Soundbar with Wireless Subwoofer and Rear Surround Speakers 500W", 34999, 21999),
            ("Compact 2.1 Channel Soundbar with Built-in Bluetooth & Optical In", 11999, 5999),
            ("Premium High Speed 8K HDMI Cable 48Gbps 3-Meter Nylon Braided", 1999, 899),
            ("TV Ambient Backlight Immersion Camera Sync RGB LED Strip 55-65", 8999, 4999),
            ("Wireless Multiroom Audio Receiver with AirPlay 2 & Spotify Connect", 11999, 6999),
            ("Smart TV Remote Control Replacement with Voice Command", 1499, 699),
            ("Anti-Glare Matte Screen Protector Filter for 55-inch TV", 4999, 2499),
            ("Digital TV Antenna Indoor Amplified 120 Miles Range 4K 1080p", 2499, 1199),
            ("Component Audio Video AV Receiver 7.2ch 8K eARC Dolby Atmos", 69990, 49990)
        ]
    },
    "Computer Peripherals & Storage": {
        "price_min": 799,
        "price_max": 35000,
        "brands": ["SanDisk", "Crucial", "Seagate", "Western Digital", "Kingston", "Keychron", "Logitech", "LG", "ASUS", "Corsair"],
        "items": [
            ("1TB NVMe M.2 PCIe 4.0 Internal SSD up to 5000MB/s Speed", 11500, 6299),
            ("2TB External Portable Hard Drive USB 3.0 Password Protection", 8999, 5799),
            ("27-inch QHD IPS 144Hz 1ms Gaming Monitor HDR10 FreeSync", 32000, 21999),
            ("Wireless Ergonomic Performance Mouse with MagSpeed Scroll Wheel", 10995, 7995),
            ("Wireless Mechanical Keyboard Hot-Swappable Gateron Switches", 9999, 7499),
            ("Full HD 1080p 60fps Streaming Webcam with Stereo Microphone", 8995, 5995),
            ("11-in-1 Multiport USB-C Docking Station with Dual 4K HDMI 100W", 12999, 8499),
            ("32-inch 4K UHD Curved Monitor with Built-in Speakers", 34990, 26990),
            ("DDR5 32GB (2x16GB) 6000MHz Desktop RAM Memory Kit", 14999, 9999),
            ("2TB Extreme Portable External Rugged SSD USB-C 1050MB/s", 28000, 16999),
            ("24-inch FHD IPS 100Hz Borderless Eye-Care Office Monitor", 14999, 8999),
            ("Silent Wireless Keyboard and Mouse Set with Number Pad", 3495, 2195),
            ("Vertical Ergonomic Wireless Mouse 57-Degree Natural Posture", 4995, 3495),
            ("PCIe Wi-Fi 6E Dual Band Desktop Network Card with Bluetooth 5.3", 4499, 2499),
            ("1000W 80 Plus Gold Fully Modular ATX Power Supply PSU", 16999, 11999),
            ("All-in-One Liquid CPU Cooler 240mm RGB Dual PWM Fans", 9999, 6499),
            ("Dual Bay External Hard Drive Docking Station with Offline Clone", 4999, 2899),
            ("Mechanical Numpad Numeric Keypad Wireless Bluetooth 2.4GHz", 2999, 1699),
            ("High Speed Gigabit Ethernet Switch 8 Ports Metal Housing", 2999, 1499),
            ("Large Micro-Weave Cloth Gaming Mouse Pad 450x400mm", 1499, 699)
        ]
    }
}

VARIANTS = [
    ("Midnight Black", "Standard Edition"),
    ("Space Gray", "Pro Edition"),
    ("Arctic White", "V2 Upgrade"),
    ("Navy Blue", "Compact Edition"),
    ("Titanium Silver", "Special Edition"),
    ("Matte Black", "Plus Edition"),
    ("Graphite", "2024 Edition"),
    ("Rose Gold", "Ultra Edition")
]

FEATURES = [
    "with Fast Charging",
    "with 2-Year Warranty",
    "with Smart App Support",
    "with Aluminum Unibody",
    "High Durability Edition",
    "with Auto Power Off",
    "with Ultra-Low Latency",
    "Certified Energy Efficient"
]


def generate_large_product_dataset(target_per_category: int = 120) -> Path:
    """
    Generates target_per_category unique Amazon products per category (12 categories * 120 = 1,440 products)
    with realistic prices, discounts between 5% and 60%, star ratings, and review counts.
    """
    csv_path = config.RAW_PRODUCTS_CSV
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    seen_names = set()
    prod_counter = 1001

    categories = list(CATEGORY_SPECS.keys())

    for category in categories:
        spec = CATEGORY_SPECS[category]
        brands = spec["brands"]
        items = spec["items"]
        p_min = spec["price_min"]
        p_max = spec["price_max"]

        cat_generated = 0
        iteration = 0

        while cat_generated < target_per_category and iteration < 2000:
            iteration += 1
            brand = random.choice(brands)
            base_item = random.choice(items)
            item_desc, base_act, base_disc = base_item
            variant_color, variant_tier = random.choice(VARIANTS)
            feature = random.choice(FEATURES)

            pattern = random.randint(1, 4)
            if pattern == 1:
                title = f"{brand} {item_desc} - {variant_color} ({variant_tier})"
            elif pattern == 2:
                title = f"{brand} {variant_tier} {item_desc} {feature}"
            elif pattern == 3:
                title = f"{brand} {item_desc} ({variant_color}, {feature})"
            else:
                title = f"{brand} {variant_color} {item_desc} - {variant_tier}"

            if title in seen_names:
                continue
            seen_names.add(title)

            # Realistic pricing strictly within category bounds
            jitter = random.uniform(0.85, 1.20)
            actual_price = round(max(p_min, min(p_max, base_act * jitter)))

            # Discount percentage strictly between 5% and 60%
            discount_pct = random.randint(8, 55)
            discounted_price = round(actual_price * (1.0 - (discount_pct / 100.0)))
            if discounted_price >= actual_price:
                discounted_price = actual_price - 50

            exact_pct = round(((actual_price - discounted_price) / actual_price) * 100)

            # Rating: 3.6 to 4.8
            rating = round(random.triangular(3.6, 4.8, 4.3), 1)

            # Rating count: 120 to 220,000
            rating_count = int(random.lognormvariate(8.5, 1.4))
            rating_count = max(50, min(280000, rating_count))

            prod_id = f"AMZN-{category[:3].upper()}-{prod_counter}"
            prod_counter += 1

            rows.append({
                "product_id": prod_id,
                "product_name": title,
                "category": category,
                "actual_price": f"₹{actual_price:,}",
                "discounted_price": f"₹{discounted_price:,}",
                "discount_percentage": f"{exact_pct}%",
                "rating": rating,
                "rating_count": f"{rating_count:,}"
            })
            cat_generated += 1

    # Add 1 deliberate duplicate and 1 formatted space row to test ETL data quality
    rows.append(rows[0].copy())
    rows.append({
        "product_id": "AMZN-QC-9999",
        "product_name": "  SanDisk 512GB Extreme PRO UHS-I microSDXC Memory Card with Adapter   ",
        "category": "Computer Peripherals & Storage",
        "actual_price": " ₹ 7,500 ",
        "discounted_price": " ₹ 3,999 ",
        "discount_percentage": " 47% ",
        "rating": 4.6,
        "rating_count": " 124,500 "
    })

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "product_id",
            "product_name",
            "category",
            "actual_price",
            "discounted_price",
            "discount_percentage",
            "rating",
            "rating_count"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully generated {len(rows)} raw product records in {csv_path}")
    print(f"Total Unique Products: {len(seen_names)}")
    print(f"Total Categories: {len(CATEGORY_SPECS)}")
    return csv_path


if __name__ == "__main__":
    generate_large_product_dataset(target_per_category=120)

"""The curated RMIT Store catalogue used by `manage.py seed_demo`.

Why this file exists
--------------------
The seeder used to build the catalogue out of Faker: product names came from
`faker.catch_phrase()`, descriptions from `faker.paragraph()`, and the
photograph was drawn from a shuffled pool with no relationship to either. The
result was a store selling "Polarized 24/7 Intranet" for $16.03, illustrated
with a picture of a graduation teddy bear, reviewed with lorem ipsum.

That is fine for exercising pagination and quite bad for everything else: you
cannot sanity-check a deployment against a catalogue whose own data makes no
sense, and screenshots of it are unusable in course material.

Each of the 47 photographs in `seed_assets/products/` is a real RMIT
merchandise shot. Every entry below names the photograph it belongs to, so the
image, the name, the description, the category and the reviews all agree with
each other.

Layout
------
`PRODUCTS` holds the 42 products in the main catalogue. `MERCHANT_PRODUCTS`
holds the 5 that belong to the demo seller's "Campus Threads" brand - printed
tees and a graphic hoodie, which is what a student-run printing label would
plausibly sell. Between them every photograph is used exactly once, so no two
products in the shop share an image.

`image` is the number N in `seed_assets/products/p-N.jpg`.
`kind` selects the review pool in REVIEWS_BY_KIND, so a hoodie gets reviews
about fleece weight and sizing rather than about ink quality.
"""

# --- categories ------------------------------------------------------------
# 15 categories, every one of them with products in it. The storefront filter
# is only meaningful if selecting a category actually narrows the results.

CATEGORIES = [
    ("Hoodies & Sweatshirts", "Fleece pullovers, crews and zip-throughs in the RMIT palette."),
    ("T-Shirts", "Printed and embroidered cotton tees."),
    ("Polo Shirts", "Collared shirts for staff, students and open days."),
    ("Jackets & Outerwear", "Layers for a Melbourne winter, plus laboratory coats."),
    ("Activewear", "Training and running gear built for the gym and the track."),
    ("Team & Club Wear", "Heritage jerseys and club kit for RMIT teams."),
    ("Bags & Totes", "Carry your laptop, your library books and your lunch."),
    ("Headwear", "Caps and hats carrying the RMIT and Redbacks marks."),
    ("Lanyards & ID Holders", "Keep your student card where you can find it."),
    ("Stationery & Notebooks", "Exercise books, journals, pens and study packs."),
    ("Tech & Power", "Keep your devices charged between lectures."),
    ("Pins & Badges", "Enamel pins for your discipline, your college and your lapel."),
    ("Graduation", "Frames, bears and keepsakes for the end of the degree."),
    ("Gifts & Souvenirs", "Something to take home, or to send overseas."),
    ("Everyday Accessories", "The small things - keyrings, umbrellas and masks."),
]

# --- brands ----------------------------------------------------------------
# 15 brands. "Campus Threads" is deliberately NOT in this list: it is created
# in seed_demo._create_demo_users() and owned by the demo merchant, and the
# seeder relies on `Brand.objects.filter(merchant__isnull=True)` to tell the
# house brands apart from seller-owned ones.

BRANDS = [
    ("RMIT Official", "The university's own range of apparel and gifts."),
    ("RMIT Redbacks", "Kit for RMIT's sporting clubs and teams."),
    ("RMIT Sport", "Training and performance wear for the fitness centres."),
    ("RMIT Alumni", "Keepsakes and gifts for graduates of the university."),
    ("RMIT Design Hub", "Small-run pieces from the design school's studios."),
    ("City Campus Co.", "Everyday essentials for the Swanston Street campus."),
    ("Bundoora Basics", "Hard-wearing staples, made for the northern campus."),
    ("Brunswick Made", "Textile work from the Brunswick campus workshops."),
    ("Swanston Studio", "Graphic apparel drawn by students in the city."),
    ("Storey Hall Supply", "Stationery and desk goods for the studious."),
    ("La Trobe Lane", "Bags, totes and carry goods."),
    ("Melbourne Made", "Locally manufactured accessories and homewares."),
    ("Novo Collective", "Sustainable basics in organic cotton."),
    ("Southbank Supply", "Materials and workwear for the arts precinct."),
    ("Capitol Print Co.", "Screen-printed tees, posters and pins."),
]

# --- products --------------------------------------------------------------
# `taxable` mixes deliberately. Apparel and accessories are taxable; books,
# exercise books and study materials are not. Acceptance journey B in the
# README asks you to buy one of each and check the tax arithmetic by hand,
# which only works if the catalogue contains both.

PRODUCTS = [
    # -- hoodies and sweatshirts --
    dict(image=1, sku="RM-HOOD-001", name="RMIT Classic Pullover Hoodie - Black",
         price="89.95", quantity=64, taxable=True, kind="apparel",
         brand="RMIT Official", categories=["Hoodies & Sweatshirts"],
         description="A heavyweight 320gsm cotton-rich fleece with a lined hood, "
                     "kangaroo pocket and the embroidered RMIT logo on the chest. "
                     "Cut straight through the body so it layers over a shirt "
                     "without pulling. Unisex sizing, XS to 3XL."),
    dict(image=2, sku="RM-HOOD-002", name="RMIT Zip-Through Hoodie - Grey Marle",
         price="94.95", quantity=48, taxable=True, kind="apparel",
         brand="RMIT Official", categories=["Hoodies & Sweatshirts", "Jackets & Outerwear"],
         description="Full-length YKK zip, brushed fleece backing and ribbed cuffs "
                     "that stay put. The drawcords are flat woven rather than round, "
                     "so they don't work themselves out of the hood in the wash."),
    dict(image=4, sku="RM-HOOD-003", name="RMIT Zip Hoodie - Cobalt Blue",
         price="94.95", quantity=37, taxable=True, kind="apparel",
         brand="RMIT Official", categories=["Hoodies & Sweatshirts", "Jackets & Outerwear"],
         description="The zip-through in the university's cobalt, with a woven RMIT "
                     "badge at the left chest. Mid-weight, so it works as an outer "
                     "layer in autumn and under a coat in July."),
    dict(image=13, sku="RM-HOOD-004", name="RMIT Campus Hoodie - Charcoal",
         price="84.95", quantity=52, taxable=True, kind="apparel",
         brand="Bundoora Basics", categories=["Hoodies & Sweatshirts"],
         description="A softer, lighter pullover than the Classic - 280gsm, with a "
                     "relaxed shoulder and a slightly cropped body. Pre-shrunk, so "
                     "the length you buy is the length you keep."),
    dict(image=16, sku="RM-HOOD-005", name="RMIT Crew Sweatshirt - Olive",
         price="79.95", quantity=41, taxable=True, kind="apparel",
         brand="Novo Collective", categories=["Hoodies & Sweatshirts"],
         description="Organic cotton crew neck in a muted olive, with a tonal "
                     "embroidered logo. No hood, no pocket, nothing to catch on a "
                     "lab bench."),
    dict(image=17, sku="RM-HOOD-006", name="RMIT Crew Sweatshirt - Steel Blue",
         price="79.95", quantity=44, taxable=True, kind="apparel",
         brand="Brunswick Made", categories=["Hoodies & Sweatshirts"],
         description="The organic cotton crew in steel blue. Ribbed neckline holds "
                     "its shape, and the body is long enough to sit past the hip."),
    dict(image=24, sku="RM-HOOD-007", name="RMIT Campus Hoodie - Cream",
         price="84.95", quantity=29, taxable=True, kind="apparel",
         brand="Swanston Studio", categories=["Hoodies & Sweatshirts"],
         description="Undyed cream fleece with the RMIT wordmark printed in navy. "
                     "The lightest colour in the range and the one that shows a "
                     "coffee accident most, so buy accordingly."),
    dict(image=27, sku="RM-HOOD-008", name="RMIT Crew Sweatshirt - Black",
         price="79.95", quantity=58, taxable=True, kind="apparel",
         brand="RMIT Official", categories=["Hoodies & Sweatshirts"],
         description="The plainest thing in the catalogue and the best selling. "
                     "Heavy black crew, small embroidered logo, nothing else."),
    dict(image=28, sku="RM-HOOD-009", name="RMIT Crew Sweatshirt - Ivory",
         price="79.95", quantity=33, taxable=True, kind="apparel",
         brand="Novo Collective", categories=["Hoodies & Sweatshirts"],
         description="Ivory crew in organic cotton with a garment-dyed finish, so "
                     "each one sits very slightly differently in tone."),
    dict(image=29, sku="RM-HOOD-010", name="RMIT Zip Hoodie - Grey Marle",
         price="99.95", quantity=26, taxable=True, kind="apparel",
         brand="RMIT Sport", categories=["Hoodies & Sweatshirts", "Activewear"],
         description="A heavier zip-through built for standing on the sideline in "
                     "the cold. Deep hood, zipped side pockets and a brushed inner "
                     "face that holds warmth without adding bulk."),
    dict(image=30, sku="RM-HOOD-011", name="RMIT Pullover Hoodie - Silver Grey",
         price="89.95", quantity=47, taxable=True, kind="apparel",
         brand="RMIT Official", categories=["Hoodies & Sweatshirts"],
         description="The Classic pullover in silver grey, with the wordmark "
                     "printed large across the chest in white."),

    # -- polos --
    dict(image=5, sku="RM-POLO-001", name="RMIT Women's Polo - Black",
         price="59.95", quantity=54, taxable=True, kind="polo",
         brand="RMIT Official", categories=["Polo Shirts"],
         description="Fitted through the waist with a three-button placket and a "
                     "self-fabric collar that survives the wash. Embroidered logo "
                     "at the left chest."),
    dict(image=21, sku="RM-POLO-002", name="RMIT Men's Polo - Black",
         price="59.95", quantity=61, taxable=True, kind="polo",
         brand="RMIT Official", categories=["Polo Shirts"],
         description="Straight-cut cotton piqué polo in black, with side vents and "
                     "a two-button placket. The everyday staff shirt."),
    dict(image=15, sku="RM-POLO-003", name="RMIT Sports Polo - White",
         price="64.95", quantity=38, taxable=True, kind="polo",
         brand="RMIT Redbacks", categories=["Polo Shirts", "Activewear"],
         description="Moisture-wicking polyester knit in white with red and navy "
                     "trim at the collar. Worn by RMIT club teams on match day."),
    dict(image=37, sku="RM-POLO-004", name="RMIT School of Education Polo",
         price="64.95", quantity=22, taxable=True, kind="polo",
         brand="RMIT Official", categories=["Polo Shirts"],
         description="Navy polo with contrast white side panels and the School of "
                     "Education lock-up embroidered beneath the RMIT logo. Made for "
                     "placement and practicum."),
    dict(image=38, sku="RM-POLO-005", name="RMIT Faculty Polo - Navy",
         price="62.95", quantity=45, taxable=True, kind="polo",
         brand="RMIT Official", categories=["Polo Shirts"],
         description="The standard navy faculty polo, unisex sizing, with a plain "
                     "embroidered logo and no faculty lock-up - order this one if "
                     "you want it to outlast a restructure."),
    dict(image=39, sku="RM-POLO-006", name="RMIT Sports Polo - Navy",
         price="64.95", quantity=36, taxable=True, kind="polo",
         brand="RMIT Sport", categories=["Polo Shirts", "Activewear"],
         description="Navy performance polo with raglan sleeves and mesh underarm "
                     "panels. Cut long in the body so it stays tucked."),
    dict(image=40, sku="RM-POLO-007", name="RMIT Women's Sports Polo - Navy",
         price="64.95", quantity=31, taxable=True, kind="polo",
         brand="RMIT Sport", categories=["Polo Shirts", "Activewear"],
         description="The performance polo cut for a woman's fit, with a shaped "
                     "hem and a softer collar stand."),

    # -- team, activewear, outerwear --
    dict(image=3, sku="RM-TEAM-001", name="RMIT Heritage Rugby Jersey",
         price="129.95", quantity=18, taxable=True, kind="apparel",
         brand="RMIT Redbacks", categories=["Team & Club Wear", "Hoodies & Sweatshirts"],
         description="A reproduction of the 1970s RMIT jersey in heavy brushed "
                     "cotton, with the twill numbering and rubber buttons of the "
                     "original. Built to be worn, not framed."),
    dict(image=31, sku="RM-ACTV-001", name="RMIT Training Singlet - Men's",
         price="44.95", quantity=42, taxable=True, kind="activewear",
         brand="RMIT Sport", categories=["Activewear"],
         description="Lightweight training singlet with a dropped armhole and a "
                     "mesh back panel. Prints stay flat under a barbell."),
    dict(image=32, sku="RM-ACTV-002", name="RMIT Running Singlet - Women's",
         price="44.95", quantity=39, taxable=True, kind="activewear",
         brand="RMIT Sport", categories=["Activewear"],
         description="Race-cut singlet in a quick-drying knit, with flatlock seams "
                     "at the shoulder so it doesn't chafe over ten kilometres."),
    dict(image=26, sku="RM-JACK-001", name="RMIT Lightweight Jacket - Navy",
         price="139.95", quantity=24, taxable=True, kind="apparel",
         brand="City Campus Co.", categories=["Jackets & Outerwear"],
         description="A packable shell that folds into its own pocket. Taped seams "
                     "and a two-way zip; enough for the walk from Building 80 to "
                     "the tram in the rain."),
    dict(image=20, sku="RM-LABC-001", name="RMIT Laboratory Coat",
         price="54.95", quantity=76, taxable=True, kind="labcoat",
         brand="Southbank Supply", categories=["Jackets & Outerwear"],
         description="Standard-issue white lab coat in poly-cotton drill, with "
                     "three pockets, a pen slot and press studs rather than buttons "
                     "so it comes off quickly. Required for most wet labs."),

    # -- bags, headwear, lanyards --
    dict(image=14, sku="RM-BAGS-001", name="RMIT Canvas Tote Bag",
         price="24.95", quantity=120, taxable=True, kind="bag",
         brand="La Trobe Lane", categories=["Bags & Totes"],
         description="Unbleached 12oz cotton canvas with long shoulder-length "
                     "handles and a boxed base, so it stands up on the desk instead "
                     "of collapsing. Holds a 15-inch laptop flat."),
    dict(image=9, sku="RM-HEAD-001", name="RMIT Redbacks Cap",
         price="34.95", quantity=67, taxable=True, kind="headwear",
         brand="RMIT Redbacks", categories=["Headwear", "Team & Club Wear"],
         description="Six-panel cotton twill cap in maroon with the Redbacks mark "
                     "embroidered at the front and an adjustable metal clasp."),
    dict(image=22, sku="RM-LANY-001", name="RMIT Lanyard with ID Card Holder",
         price="12.95", quantity=180, taxable=True, kind="accessory",
         brand="City Campus Co.", categories=["Lanyards & ID Holders"],
         description="Woven lanyard with a safety breakaway at the back of the neck "
                     "and a clear rigid card holder. The clip is a swivel hook, so "
                     "the card faces the reader instead of your chest."),
    dict(image=23, sku="RM-LANY-002", name="RMIT Lanyard - Assorted Colours",
         price="9.95", quantity=240, taxable=True, kind="accessory",
         brand="City Campus Co.", categories=["Lanyards & ID Holders"],
         description="The plain lanyard without the card holder, in eleven colours. "
                     "Sold single; the colour is chosen at random unless you ask at "
                     "the counter."),

    # -- stationery --
    dict(image=11, sku="RM-STAT-001", name="RMIT Student Stationery Pack",
         price="29.95", quantity=95, taxable=False, kind="stationery",
         brand="Storey Hall Supply", categories=["Stationery & Notebooks"],
         description="Two 64-page feint-ruled exercise books, a mesh pencil pouch, "
                     "a ballpoint and a lanyard. What you need on day one, in one "
                     "bag, at less than the sum of the parts."),
    dict(image=19, sku="RM-STAT-002", name="RMIT Lab Starter Kit",
         price="39.95", quantity=58, taxable=False, kind="stationery",
         brand="Southbank Supply", categories=["Stationery & Notebooks"],
         description="Exercise books, a clear zip wallet that satisfies a closed-bag "
                     "rule, and safety glasses. Pairs with the laboratory coat."),
    dict(image=18, sku="RM-NOTE-001", name="RMIT A5 Notebook Set (3-Pack)",
         price="27.95", quantity=88, taxable=False, kind="stationery",
         brand="Storey Hall Supply", categories=["Stationery & Notebooks"],
         description="Three A5 notebooks in navy, grey and red, 96 pages each, "
                     "with a debossed logo and a sewn binding that lets the book "
                     "lie flat. Ruled, not dotted."),
    dict(image=12, sku="RM-PENS-001", name="RMIT Pen and Stylus Gift Set",
         price="34.95", quantity=64, taxable=True, kind="stationery",
         brand="Melbourne Made", categories=["Stationery & Notebooks", "Gifts & Souvenirs"],
         description="A brushed metal ballpoint and a capacitive stylus in a hinged "
                     "presentation box. Takes a standard Parker-style refill, so it "
                     "outlives the ink it ships with."),

    # -- tech and accessories --
    dict(image=6, sku="RM-TECH-001", name="RMIT Power Bank 10,000mAh",
         price="49.95", quantity=52, taxable=True, kind="tech",
         brand="Melbourne Made", categories=["Tech & Power"],
         description="A 10,000mAh bank with USB-C in and out plus a USB-A port, and "
                     "a short braided cable in the box. Enough for two full phone "
                     "charges, and it fits in the tote's inner pocket."),
    dict(image=10, sku="RM-ACCS-001", name="RMIT Logo Keyring",
         price="11.95", quantity=210, taxable=True, kind="accessory",
         brand="RMIT Official", categories=["Everyday Accessories", "Gifts & Souvenirs"],
         description="A round enamelled keyring in RMIT red on a split ring, with "
                     "the logo on one face and the wordmark on the other."),
    dict(image=46, sku="RM-ACCS-002", name="RMIT Compact Umbrella",
         price="32.95", quantity=73, taxable=True, kind="accessory",
         brand="Melbourne Made", categories=["Everyday Accessories"],
         description="A two-fold umbrella with a fibreglass frame that inverts "
                     "instead of snapping when the wind comes down Swanston Street. "
                     "Folds to 30cm and comes with a sleeve."),
    dict(image=7, sku="RM-ACCS-003", name="RMIT Reusable Face Mask (3-Pack)",
         price="19.95", quantity=140, taxable=False, kind="accessory",
         brand="City Campus Co.", categories=["Everyday Accessories"],
         description="Three-layer cotton masks with an adjustable ear loop and a "
                     "nose wire. Washable at 60 degrees; sold in packs of three so "
                     "one is always clean."),

    # -- pins --
    dict(image=41, sku="RM-PINS-001", name="RMIT Discipline Enamel Pin Set",
         price="26.95", quantity=49, taxable=True, kind="pin",
         brand="RMIT Design Hub", categories=["Pins & Badges", "Gifts & Souvenirs"],
         description="Five hard-enamel pins, one for each of Pharmacy, Design, "
                     "Social Sciences, Engineering and Business, on a printed backing "
                     "card. Butterfly clutches, not rubber."),
    dict(image=42, sku="RM-PINS-002", name="RMIT Logo Enamel Pin",
         price="12.95", quantity=130, taxable=True, kind="pin",
         brand="Capitol Print Co.", categories=["Pins & Badges"],
         description="The RMIT mark in hard enamel on a gold-plated base, 20mm "
                     "across, with a locking pin back that will not shed itself on "
                     "the tram."),

    # -- graduation and gifts --
    dict(image=43, sku="RM-GRAD-001", name="RMIT Graduation Certificate Frame",
         price="89.95", quantity=34, taxable=True, kind="graduation",
         brand="RMIT Alumni", categories=["Graduation"],
         description="A black timber frame with a gold inner fillet, cut to the "
                     "exact size of an RMIT testamur. Conservation-grade matting, so "
                     "the paper does not yellow against the board."),
    dict(image=44, sku="RM-GRAD-002", name="RMIT Testamur Frame - Timber",
         price="99.95", quantity=27, taxable=True, kind="graduation",
         brand="RMIT Alumni", categories=["Graduation"],
         description="The same testamur sizing in a natural timber moulding, with "
                     "a double mat in RMIT red and a hanging fitting for both "
                     "portrait and landscape."),
    dict(image=45, sku="RM-GRAD-003", name="RMIT Graduation Frame and Bear Gift Set",
         price="119.95", quantity=21, taxable=True, kind="graduation",
         brand="RMIT Alumni", categories=["Graduation", "Gifts & Souvenirs"],
         description="The certificate frame boxed with the graduation bear, which "
                     "is what most families end up buying separately about an hour "
                     "after the ceremony."),
    dict(image=47, sku="RM-GRAD-004", name="RMIT Graduation Bear",
         price="39.95", quantity=86, taxable=True, kind="gift",
         brand="RMIT Alumni", categories=["Graduation", "Gifts & Souvenirs"],
         description="A jointed plush bear in a black academic gown and trencher "
                     "cap, with an RMIT-red stole. Twenty-two centimetres seated."),
    dict(image=8, sku="RM-GIFT-001", name="RMIT Koala Plush Toy",
         price="29.95", quantity=104, taxable=True, kind="gift",
         brand="RMIT Official", categories=["Gifts & Souvenirs"],
         description="A soft-filled koala in a miniature RMIT hoodie, which is the "
                     "single most posted-overseas item in the shop. Surface washable, "
                     "suitable for ages three and up."),
]

# The demo merchant's own products. "Campus Threads" is described in the seeder
# as a student-run label printing sustainable RMIT apparel, so it gets exactly
# that: printed tees and one graphic hoodie.

MERCHANT_PRODUCTS = [
    dict(image=33, sku="CT-TEES-001", name="RMIT Progress Pride T-Shirt",
         price="42.95", quantity=48, taxable=True, kind="tee",
         categories=["T-Shirts"],
         description="The Progress Pride chevron screen-printed across the chest on "
                     "a heavyweight organic cotton tee. Printed in Brunswick with "
                     "water-based inks that sit in the fabric rather than on it."),
    dict(image=34, sku="CT-TEES-002", name="RMIT Pride Logo T-Shirt",
         price="39.95", quantity=55, taxable=True, kind="tee",
         categories=["T-Shirts"],
         description="The RMIT mark reworked in the pride colours as a small "
                     "left-chest print. Unisex fit, pre-shrunk, mid-weight 190gsm "
                     "cotton."),
    dict(image=35, sku="CT-TEES-003", name="RMIT Melbourne Illustrated T-Shirt",
         price="44.95", quantity=37, taxable=True, kind="tee",
         categories=["T-Shirts"],
         description="A hand-drawn map of the city campus and its landmarks, printed "
                     "in RMIT red across the front. Drawn by a Communication Design "
                     "student and reprinted every year."),
    dict(image=36, sku="CT-TEES-004", name="RMIT City Campus T-Shirt",
         price="44.95", quantity=42, taxable=True, kind="tee",
         categories=["T-Shirts"],
         description="The illustrated print in a scattered layout across the whole "
                     "front panel - trams, Storey Hall, the Old Melbourne Gaol wall "
                     "and a very small koala."),
    dict(image=25, sku="CT-HOOD-001", name="Campus Threads Graphic Hoodie - Black",
         price="99.95", quantity=23, taxable=True, kind="apparel",
         categories=["Hoodies & Sweatshirts"],
         description="A black heavyweight pullover with a tonal circular print "
                     "across the chest, printed in a run of one hundred. Organic "
                     "cotton shell with a recycled-polyester fleece backing."),
]

# --- reviews ---------------------------------------------------------------
# Keyed by the `kind` on each product, so the review text is about the thing
# being reviewed. Each entry is (rating, title, body).
#
# The distribution is deliberately not all five stars: the shop page has a
# "4 stars & up" filter and a sort, and neither can be verified against a
# catalogue where every product scores the same.

REVIEWS_BY_KIND = {
    "apparel": [
        (5, "Warmer than it looks", "The fleece is genuinely heavy - I wore it through a Melbourne winter with just a shirt underneath. Washed it a dozen times and the cuffs still grip."),
        (5, "True to the size chart", "I measured against the chart rather than guessing and the medium is spot on. Sleeves are long enough, which is rare for me."),
        (4, "Great, but size up", "Lovely fabric and the embroidery is neat. It came up slightly snug across the shoulders, so I swapped for the large and that was right."),
        (4, "Holds its shape", "No pilling after a term of constant wear. Only reason it isn't five stars is the hood sits a little flat."),
        (3, "Colour is darker in person", "Perfectly good sweatshirt, but the photo reads lighter than what arrived. Not a problem once I stopped expecting the photo."),
        (5, "Bought a second one", "Wore the first one so much I bought the same again in another colour. That is the whole review."),
        (2, "Shrank in the dryer", "My fault for not reading the label - it is cold wash and hang dry. Line dried since and it has been fine, but be warned."),
    ],
    "polo": [
        (5, "Collar actually survives", "Most polos go floppy at the collar after a few washes. This one has held up all semester and still looks tidy for placement."),
        (4, "Smart enough for teaching", "Wear it on campus twice a week. Breathes well in a warm room and the embroidery is clean."),
        (4, "Good fit, slightly long", "Fits well through the chest. A touch long in the body if you plan to wear it untucked."),
        (5, "Exactly the right navy", "Matches the rest of the faculty kit, which was the point. Quick delivery too."),
        (3, "Fine, nothing special", "Does the job and looks correct. The fabric is a little thin for the price."),
    ],
    "tee": [
        (5, "Print quality is excellent", "The ink is soft to the touch rather than a plastic slab, and it has not cracked after a lot of washing."),
        (5, "Lovely design", "Got stopped twice on campus to be asked where it came from. The drawing is genuinely nice."),
        (4, "Good weight for the price", "Not a thin promotional tee - this has some substance. Fits true to size."),
        (4, "Happy with it", "Print is crisp and the cotton is soft. Would like it in more colours."),
        (3, "Runs a bit boxy", "The print is great but the cut is wide and short on me. Fine if that is the look you want."),
    ],
    "activewear": [
        (5, "Doesn't chafe", "Ran a half marathon in it with no rubbing at the shoulders at all. The flatlock seams do what they claim."),
        (4, "Dries quickly", "Soaked it at the gym and it was dry by the time I got home. Slightly loose at the armhole for me."),
        (5, "Light and cool", "Barely notice it in a hot session. Print has survived a lot of washes."),
        (4, "Good value", "Cheaper than the big sports brands and honestly performs the same."),
    ],
    "labcoat": [
        (5, "Meets the lab requirement", "Passed the safety check first time. Press studs are much better than buttons when you need it off quickly."),
        (4, "Good pockets", "Fits over a jumper, which matters in a cold lab. Sleeves are a fraction long on me but the cuff holds them back."),
        (4, "Washes clean", "A stain came out on a normal warm cycle. Still white after a semester."),
        (3, "Sizing is generous", "Order one size down from your usual. Otherwise no complaints."),
    ],
    "bag": [
        (5, "Holds an absurd amount", "Laptop, two textbooks, lunch and a jumper, and the base still sits flat. The boxed bottom makes all the difference."),
        (5, "Handles are the right length", "Goes over the shoulder with a coat on, which most totes get wrong."),
        (4, "Sturdy canvas", "Thick, unlined and clearly built to last. Would prefer an inner pocket for keys."),
        (4, "Good everyday bag", "Using it as a shopping bag as much as a uni bag. No fraying so far."),
    ],
    "headwear": [
        (5, "Good fit and finish", "Embroidery is tight and the clasp adjusts smoothly. Sits well without being tight."),
        (4, "Nice colour", "The maroon is deeper than the photo suggests, which I prefer. Brim is stiff enough to hold its curve."),
        (4, "Does the job", "Standard cap, well made, correct logo. Not much else to say."),
    ],
    "accessory": [
        (5, "Cheap and genuinely useful", "Bought two. The breakaway clip has already saved me once when it caught on a door handle."),
        (4, "Card sits the right way round", "The swivel hook means the card faces out at the reader. Small thing, but it is the reason I bought this one."),
        (5, "Survived a real storm", "Turned inside out on Swanston Street and popped back without breaking a rib. That is all I wanted."),
        (4, "Good quality for the price", "Feels more solid than I expected. Compact enough for the side pocket of a bag."),
        (3, "Colour is random", "Works fine, but I could not choose the colour online and got one I would not have picked."),
    ],
    "stationery": [
        (5, "Cheaper than buying separately", "Worked out about ten dollars less than the same items individually. The pouch is better quality than the usual freebie."),
        (5, "Paper doesn't bleed", "Used a fountain pen and a fineliner and neither went through. Binding lies flat, which is the main thing."),
        (4, "Good value pack", "Everything a first-year actually needs. The pen is unremarkable but perfectly usable."),
        (4, "Nice notebooks", "The debossed cover looks smart and the sewn binding is holding up. Would like a dotted option."),
        (3, "Books are fairly thin", "Fine for one subject each, but I got through them faster than expected."),
    ],
    "tech": [
        (5, "Charges the laptop in a pinch", "USB-C out is fast enough to keep a laptop alive through a long lecture. Two full phone charges as advertised."),
        (4, "Compact and solid", "Slips into a jacket pocket. Gets a bit warm on a fast charge but nothing alarming."),
        (4, "Cable in the box is a nice touch", "Short braided cable saves carrying another one. Would prefer a pass-through charge."),
        (3, "Takes a while to refill", "Works well but is slow to charge itself back up overnight."),
    ],
    "pin": [
        (5, "Locking backs are worth it", "I have lost enamel pins off rubber clutches before. These have not moved."),
        (5, "Colours are crisp", "Hard enamel so the surface is smooth and the lines are sharp. Looks more expensive than it was."),
        (4, "Great little gift", "Sent one to a friend who graduated. Backing card made it easy to post flat."),
        (4, "Nice set", "Good spread of disciplines. Would like to buy them individually rather than as a set."),
    ],
    "graduation": [
        (5, "Fits the testamur exactly", "No trimming, no gaps - the mat is cut for the real certificate size. Looks proper on the wall."),
        (5, "Parents were thrilled", "Bought it on the day and had the certificate in it before we left. Well made and heavier than it looks."),
        (4, "Lovely frame", "Beautiful timber and good glass. The hanging fittings are a little fiddly to get level."),
        (4, "Good keepsake", "Exactly what it says. Arrived well packed with no damage to the corners."),
    ],
    "gift": [
        (5, "Posted it overseas", "Light enough to send airmail without a fortune in postage, and it arrived in perfect condition. Family loved it."),
        (5, "Very well made", "The stitching and the little gown are much better quality than the usual campus plush."),
        (4, "Cute and well finished", "Slightly smaller than I pictured but genuinely nicely made. Good graduation present."),
        (4, "Popular with everyone", "Bought three for the family. All accounted for and all still intact."),
    ],
}

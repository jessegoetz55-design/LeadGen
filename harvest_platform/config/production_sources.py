"""Production-ready source configurations"""

PRODUCTION_SOURCES = [
    {
        "name": "Yellow Pages US",
        "source_type": "example_direct",
        "base_url": "https://www.yellowpages.com/search",
        "pagination_type": "click_next",
        "selectors": {
            "listing_container": ".search-results .result",
            "business_name": ".business-name",
            "phone": ".phones",
            "website": ".track-visit-website",
            "address": ".street-address",
            "city": ".locality",
            "state": ".region",
            "category": ".categories a"
        },
        "rate_limit_delay": 4.0,
        "enabled": False
    },
    {
        "name": "Yelp Business Directory",
        "source_type": "example_direct",
        "base_url": "https://www.yelp.com/search",
        "pagination_type": "infinite_scroll",
        "selectors": {
            "listing_container": "[data-testid='serp-ia-card']",
            "business_name": "h3 a",
            "phone": "[data-font-weight='semibold']",
            "website": "a[href*='biz_redir']",
            "address": "address",
            "category": "[data-testid='search-result-category']"
        },
        "rate_limit_delay": 5.0,
        "enabled": False
    },
    {
        "name": "Better Business Bureau",
        "source_type": "example_direct",
        "base_url": "https://www.bbb.org/search",
        "pagination_type": "click_next",
        "selectors": {
            "listing_container": ".search-result",
            "business_name": ".business-name",
            "phone": ".phone-link",
            "website": ".website-link",
            "address": ".address"
        },
        "rate_limit_delay": 5.0,
        "enabled": False
    },
    {
        "name": "Indeed Employer Profiles",
        "source_type": "example_direct",
        "base_url": "https://www.indeed.com/companies",
        "pagination_type": "click_next",
        "selectors": {
            "listing_container": ".css-kyg8or",
            "business_name": ".css-92r8pb",
            "category": ".css-1saizt3",
            "city": ".css-1p0sjhy",
            "website": ".css-1c9erw7"
        },
        "rate_limit_delay": 5.0,
        "enabled": False
    },
    {
        "name": "Chamber of Commerce",
        "source_type": "example_direct",
        "base_url": "https://www.chamberofcommerce.com/business-directory",
        "pagination_type": "click_next",
        "selectors": {
            "listing_container": ".business-card",
            "business_name": ".business-title",
            "phone": ".business-phone",
            "address": ".business-address",
            "category": ".business-category",
            "website": ".business-website"
        },
        "rate_limit_delay": 4.0,
        "enabled": False
    },
    {
        "name": "Angi Service Providers",
        "source_type": "example_direct",
        "base_url": "https://www.angi.com/companylist/us/",
        "pagination_type": "click_next",
        "selectors": {
            "listing_container": ".company-card",
            "business_name": ".company-name",
            "phone": ".phone-number",
            "category": ".service-category",
            "city": ".service-area"
        },
        "rate_limit_delay": 5.0,
        "enabled": False
    },
    {
        "name": "Houzz Professionals",
        "source_type": "example_direct",
        "base_url": "https://www.houzz.com/professionals/",
        "pagination_type": "infinite_scroll",
        "selectors": {
            "listing_container": ".pro-card",
            "business_name": ".pro-name",
            "phone": ".contact-phone",
            "website": ".contact-website",
            "city": ".pro-location",
            "category": ".pro-specialties"
        },
        "rate_limit_delay": 6.0,
        "enabled": False
    },
    {
        "name": "Thumbtack Service Pros",
        "source_type": "example_direct",
        "base_url": "https://www.thumbtack.com/",
        "pagination_type": "infinite_scroll",
        "selectors": {
            "listing_container": "[data-test='pro-card']",
            "business_name": "[data-test='pro-name']",
            "city": "[data-test='location']",
            "category": "[data-test='services']"
        },
        "rate_limit_delay": 5.0,
        "enabled": False
    },
    {
        "name": "Zillow Real Estate Agents",
        "source_type": "example_direct",
        "base_url": "https://www.zillow.com/professionals/real-estate-agent-reviews/",
        "pagination_type": "click_next",
        "selectors": {
            "listing_container": ".ldb-contact-card",
            "business_name": ".ldb-contact-name",
            "phone": ".ldb-contact-phone",
            "email": ".ldb-contact-email",
            "website": ".ldb-contact-website",
            "city": ".ldb-contact-location"
        },
        "rate_limit_delay": 5.0,
        "enabled": False
    },
    {
        "name": "Healthgrades Providers",
        "source_type": "example_direct",
        "base_url": "https://www.healthgrades.com/",
        "pagination_type": "click_next",
        "selectors": {
            "listing_container": ".card-provider",
            "business_name": ".provider-name",
            "category": ".specialty",
            "phone": ".phone-number",
            "address": ".provider-address"
        },
        "rate_limit_delay": 6.0,
        "enabled": False
    }
]

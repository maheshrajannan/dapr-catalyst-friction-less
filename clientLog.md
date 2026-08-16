Maheshs-MacBook-Pro-3:dapr-catalyst-friction-less maheshrajannan$ curl -s -X POST localhost:8080/triage/sample | python3 -m json.tool
{
    "place": "sample",
    "count": 5,
    "results": [
        {
            "review_id": "s1",
            "classification": {
                "sentiment": "negative",
                "theme": "service",
                "urgency": "act-now",
                "summary": "Customer repeatedly experienced long wait times with no staff assistance, resulting in permanent loss of business after three occurrences."
            },
            "owner": "store-ops@corp.example"
        },
        {
            "review_id": "s2",
            "classification": {
                "sentiment": "positive",
                "theme": "service",
                "urgency": "none",
                "summary": "Customer praises fantastic staff and is impressed by the quality of lattes from the new espresso machine."
            },
            "owner": "store-ops@corp.example"
        },
        {
            "review_id": "s3",
            "classification": {
                "sentiment": "negative",
                "theme": "cleanliness",
                "urgency": "act-now",
                "summary": "Customer reported filthy bathrooms and overflowing trash in the lobby, giving a low rating of 2 out of 5."
            },
            "owner": "facilities@corp.example"
        },
        {
            "review_id": "s4",
            "classification": {
                "sentiment": "neutral",
                "theme": "pricing",
                "urgency": "monitor",
                "summary": "Customer finds the product acceptable but considers the $14 sandwich price too high compared to nearby competitors."
            },
            "owner": "pricing@corp.example"
        },
        {
            "review_id": "s5",
            "classification": {
                "sentiment": "positive",
                "theme": "product",
                "urgency": "monitor",
                "summary": "Customer enjoyed the seasonal item but requests longer stock availability as it sold out quickly."
            },
            "owner": "merchandising@corp.example"
        }
    ]
}
Maheshs-MacBook-Pro-3:dapr-catalyst-friction-less maheshrajannan$ 

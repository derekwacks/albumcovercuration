## Album cover curation and playlist maker
Term project for Columbia CS Course 6998 Cloud Computing and Big Data

# Key Architectural Components
- Web front-end: We used the Amplify javascript SDK, storing all static website files in an S3 bucket. The service is publicly available here. We decided to deploy our front-end using React-Bootstrap. This approach allowed us to decompose our code into reusable components, for example the “card-based” feature to display the album covers and metadata. We leveraged various Bootstrap elements, including the Navbar and Container system for dynamically resizing the view based on screen size and device type. We also opted to deploy GraphQL as an API, which offered key benefits in terms of page load time and overall scalability. 
- Cognito is utilized to keep a verified user-pool so users may return to previous curations over time. 
- Lex/Lambda. We have opted for a chatbot component to gather user data and preferences. This is deployed using Lex and an accompanying Lambda function to do slot filling and validation.
- Spotify API with Spotipy wrapper. We utilize this API to retrieve artist and album data, as well as to find song previews. 
- Unsplash image API. We utilize this api to query for images based on the user’s favorite animal response
- Image processing. After extracting a cover image from the api, we employ multiple lambdas to characterize images in terms of color composition. We then vectorize each album cover or user-uploaded images with 6 dimensions as the RGB values of the most prominent two colors. 
- DynamoDB. Album data as well as curations, recommendations and user-likes are stored in a single table in DynamoDB. 
- Multiple S3 buckets are used to store cover art jpegs, and text files storing album cover vectors that are utilized in our k-nearest-neighbors implementation. 
- SES. After a curation is created, a playlist is assembled from the recommended album covers and sent to the users’ email with links to song previews. 
- Several SQS queues are used between lambdas to ensure prompt responses during lex interactions and to allow for scalability of the service such that many users may search for recommendations at once. 

# User interaction flow:
- The user creates an account or logs into their existing account
- Users interact with the chatbot interface, answering posed questions, or upload images
- The service extracts applicable information from user responses, or performs analysis on the user-uploaded image, and runs several lambdas to build a relevant recommendation.
- After a curated playlist has been assembled with album art, the service posts it to the user’s library and sends it to their email.


[Link to demo](https://www.youtube.com/watch?v=ZL0-1DzyLkk "Demo Link")

[Link to service](https://dev.d2zsw1rsygdyul.amplifyapp.com "App Link")


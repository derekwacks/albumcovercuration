# Album cover curation and playlist maker
Term project for Columbia CS Course 6998 Cloud Computing and Big Data


[Link to demo](https://www.youtube.com/watch?v=ZL0-1DzyLkk "Demo Link")

[Link to service](https://dev.d2zsw1rsygdyul.amplifyapp.com "App Link")



## Key Architectural Components
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

## User interaction flow:
- The user creates an account or logs into their existing account
- Users interact with the chatbot interface, answering posed questions, or upload images
- The service extracts applicable information from user responses, or performs analysis on the user-uploaded image, and runs several lambdas to build a relevant recommendation.
- After a curated playlist has been assembled with album art, the service posts it to the user’s library and sends it to their email.




## Algorithm Walkthrough
Upon interacting with the lex bot:

For example, if the user enters “yellow, zebra, alternative”...
The entries are validated by the fulfilling lambda to ensure the color exists (a rich Matplotlib color dictionary is queried), and the animal exists (it is checked against a very large static set to ensure the animal image query in a downstream lambda is successful). 
The user vector is created as the RGB values of yellow and the most prominent color pulled from the first image returned from a query to Unsplash for “zebra”.

The first image returned by this Unsplash query is this picture of a zebra
The top five colors (its palette) is:
[(215, 216, 218), (43, 47, 48), (102, 105, 106), (112, 116, 116), (92, 100, 100)]

Therefore the user vector becomes:
- user vector: 255 255 0 215 216 218

The first three slots represent the RGB values for yellow [255, 255, 0], and the second three slots represent the top color from the animal image (in this case: [215, 216, 218]).

Next, the service implements a K-nearest-neighbors algorithm with all vectors associated with the user’s chosen genre. These vectors are pulled from a prewritten .txt file stored in S3. 

These previously determined album cover art vectors are created from the RGB values of the top two most prominent colors in each album cover. 

On the other hand, if the user chooses to upload an image, the same logic that was applied to all cover arts is used: the top two most prominent colors are pulled, and a 6-dimensional vector is created from these two RGB colors (three values each). 

Continuing with this example:
A 2D array is created from all cover art vectors of that particular genre and the closest eleven “points” in this 6-dimensional space to the user’s response-created vector are returned with their associated album ID’s. We then craft the curation entry for DynamoDB so the front-end can present the newly created curation. Ten of these closest points are presented immediately as a curation; the eleventh is saved as a recommendation to present on the user’s homepage. 

At this point, the recommendation is shown below as copied from the cloudwatch event (leaving out all extraneous data that is also included):
- Reduxer: vector = 226 232 221 83 160 159
- Other Here Comes The Cowboy Demo: vector = 172 157 144 171 136 49
- Mayonnaise: vector = 243 225 224 84 151 181
- A Letter To My Younger Self: vector = 67 75 15 216 204 170
- The slow rush: vector = 147 34 17 199 185 164
- We Are the 21st Century Ambassadors of Peace & Magic: vector = 179 29 29 228 226 225
- Hozier: vector = 119 103 83 151 180 195
- Songs from the west coast: vector = 111 87 49 208 204 203
- Dirty Heads: vector = 194 114 25 240 225 206
- How To Be A Human Being = vector = 209 129 61 246 233 200

The albums shown above were the closest 10 points to the user vector 255 255 0 215 216 218 using each vector element as a coordinate in 6D space. 

As the user “likes” cover art in their curations, a lambda scans the DynamoDB instance every hour for these likes and adds recommended albums to the database. Users can view their personalized recommendations on the homepage. For example, if the user likes an album by Milky Chance, the service will recommend other cover art by Milky Chance not already present in the recommendation list. 

The recommendation list on the homepage is treated as a FIFO queue: as more curations are made, the service adds new recommendations based on past curations, removing the oldest items from the list. 

The service scales such that new albums may be added to the database in which case new curation requests with previously used responses will result in updated curations. 


## Architecture Diagram:
[Architecture Diagram file](./Project_Architecture.png)





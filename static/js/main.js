// Đăng ký sự kiện cho phân trang khi trang đã tải xong
document.addEventListener("DOMContentLoaded", function () {
  const nextpage = document.getElementById("nextPage");
  if (nextpage) {
    nextpage.addEventListener("click", function (e) {
      e.preventDefault();
      const urlParams = new URLSearchParams(window.location.search);
      let currentPage = parseInt(urlParams.get('page')) || 1;
      urlParams.set('page', currentPage + 1);
      window.location.href = '?' + urlParams.toString();
    });
  }

  const prevpage = document.getElementById("prevPage");
  if (prevpage) {
    prevpage.addEventListener("click", function (e) {
      e.preventDefault();
      const urlParams = new URLSearchParams(window.location.search);
      let currentPage = parseInt(urlParams.get('page')) || 1;
      urlParams.set('page', Math.max(1, currentPage - 1));
      window.location.href = '?' + urlParams.toString();
    });
  }

  const lastpage = document.getElementById("lastPage");
  if (lastpage) {
    lastpage.addEventListener("click", function (e) {
      e.preventDefault();
      const urlParams = new URLSearchParams(window.location.search);
      let counterpageText = document.getElementById("counterpage").textContent;
      let parts = counterpageText.split('/');
      let lastPage = parts.length > 1 ? parseInt(parts[1].trim()) : 1;
      urlParams.set('page', lastPage);
      window.location.href = '?' + urlParams.toString();
    });
  }

  const firstpage = document.getElementById("firstPage");
  if (firstpage) {
    firstpage.addEventListener("click", function (e) {
      e.preventDefault();
      const urlParams = new URLSearchParams(window.location.search);
      urlParams.set('page', 1);
      window.location.href = '?' + urlParams.toString();
    });
  }
});
// Các hàm cập nhật phân trang đã được tích hợp trực tiếp vào event listeners

function hideSearch() {
  document.querySelector('.textRelated').style.display = 'none';
}
const textSearch = document.querySelector(".textRelated");
const checkboxes = document.querySelectorAll('.checkbox-item');
const searchBtn = document.querySelectorAll(".search_btn");

function handleCheckboxChange(changedCheckbox) {
  checkboxes.forEach(checkbox => {
    if (checkbox !== changedCheckbox) {
      checkbox.checked = false;
    }
    if (changedCheckbox.id == "Clip") {
      faissChoose.disabled = false;
    } else {
      faissChoose.disabled = true;
    }
  });
}

checkboxes.forEach(checkbox => {
  checkbox.addEventListener('change', function () {
    if (this.checked) {
      handleCheckboxChange(this);
      
      // Toggle input display for Multi-Context
      if (this.id === 'MultiContext') {
        document.getElementById('singleContextInput').style.display = 'none';
        document.getElementById('multiContextInputs').style.display = 'block';
        document.getElementById('imageSearchInput').style.display = 'none';
      } else {
        document.getElementById('singleContextInput').style.display = 'block';
        document.getElementById('multiContextInputs').style.display = 'none';
        document.getElementById('imageSearchInput').style.display = 'none';
      }
    }
  });
});

document.querySelectorAll('.mlt-search li').forEach(function (li) {
  li.addEventListener('click', function () {
    hideSearch();
    document.querySelectorAll('.mlt-search li').forEach(function (item) {
      item.classList.remove('selected');
    });
    li.classList.add('selected');
    if (li.id === 'text') {
      textSearch.style.display = 'block';
      document.getElementById('singleContextInput').style.display = 'block';
      document.getElementById('imageSearchInput').style.display = 'none';
      document.getElementById('multiContextInputs').style.display = 'none';
    }
    if (li.id === 'image') {
      textSearch.style.display = 'block';
      document.getElementById('singleContextInput').style.display = 'none';
      document.getElementById('imageSearchInput').style.display = 'block';
      document.getElementById('multiContextInputs').style.display = 'none';
      // Auto-check Clip checkbox for image search
      document.getElementById('Clip').checked = true;
      handleCheckboxChange(document.getElementById('Clip'));
    }
    if (li.id === 'object') {
      showModalObjectSearch();
    }
  });
});

searchBtn.forEach(btn => {
  btn.addEventListener('click', function () {
    // Check if image search is active
    const imageSearchActive = document.getElementById('imageSearchInput') && 
                              document.getElementById('imageSearchInput').style.display !== 'none';
    
    // If image search is active, let the other handler take care of it
    if (imageSearchActive) {
      return;
    }
    
    const searchElement = document.querySelector('#textInput');
    const searchText = searchElement.value;
    tags = getTags();
    
    // Handle Multi-Context Search
    if (document.getElementById('MultiContext') && document.getElementById('MultiContext').checked) {
      const context1 = document.getElementById('context1').value;
      const context2 = document.getElementById('context2').value;
      const context3 = document.getElementById('context3').value;
      
      if (!context1 && !context2 && !context3) {
        alert("Please enter at least one context");
        return;
      }
      
      const url = new URL('/multi-context', window.location.origin);
      url.searchParams.set('page', 1);
      if (context1) url.searchParams.set('context1', context1);
      if (context2) url.searchParams.set('context2', context2);
      if (context3) url.searchParams.set('context3', context3);
      window.location.href = url.toString();
      return;
    }
    
    if (tags.length > 0) {
      const url = new URL('/obj', window.location.origin);
      url.searchParams.set('page', 1);
      object_query = tags.map(item => `query=${encodeURIComponent(item)}`).join('&');
      url.searchParams.delete('query');
      object_query.split('&').forEach(param => {
        const [key, value] = param.split('=');
        url.searchParams.append(key, value);
      });
      window.location.href = url.toString();
    } else if (searchText && searchText != "") {
      if (document.getElementById('Clip').checked) {
        const url = new URL('/clip', window.location.origin);
        url.searchParams.set('page', 1);
        url.searchParams.set('query', searchText);
        url.searchParams.set('faiss', faissChoose.value);
        window.location.href = url.toString();
      } else if (document.getElementById('IC').checked) {
        const url = new URL('/ic', window.location.origin);
        url.searchParams.set('page', 1);
        url.searchParams.set('query', searchText);
        window.location.href = url.toString();
      } else { alert("Please select at least one search option.") }
    } else {
      alert("Please type the search text")
    }
  })
});

//faiss select
const faissChoose = document.getElementById("faiss-select");
faissChoose.disabled = true;

//object search
const addBtn = document.getElementById('addObject');
const FormObject = document.querySelector('.form-row');
const clear = document.querySelector('#clear');
addBtn.addEventListener('click', function () {
  item = document.createElement('li');
  item.classList = "row-item";
  item.innerHTML = `
  <div class="querybox">
    <input type="text" name="quantity" placeholder="Enter quantity" onclick="showDropdown(this)" oninput="showDropdown(this)">
    <ul class="dropdown"></ul>
  </div>
  <div class="querybox">
    <input type="text" name="objname" placeholder="Enter object name" onclick="showDropdown(this)" oninput="showDropdown(this)">
    <ul class="dropdown"></ul>
  </div>
  <div class="querybox">
    <input type="text" name="color" placeholder="Enter color" onclick="showDropdown(this)" oninput="showDropdown(this)">
    <ul class="dropdown"></ul>
  </div>
  <a onclick="this.parentNode.remove()">&times</a>`;
  FormObject.appendChild(item);
});

function showModalObjectSearch(src) {
  hideSlide()
  modalBox.style.display = 'block';
  overlay.style.display = 'block';
  slide3.style.display = 'block';
}

const data = {
  quantity: ["None", '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
  objname: ["None", "Accordion", "Adhesive tape", "Aircraft", "Airplane", "Alarm clock", "Alpaca", "Ambulance", "Animal", "Ant", "Antelope", "Apple", "Armadillo", "Artichoke", "Auto part", "Axe", "Backpack", "Bagel", "Baked goods", "Balance beam", "Ball", "Balloon", "Banana", "Band-aid", "Banjo", "Barge", "Barrel", "Baseball bat", "Baseball glove", "Bat (Animal)", "Bathroom accessory", "Bathroom cabinet", "Bathtub", "Beaker", "Bear", "Bed", "Bee", "Beehive", "Beer", "Beetle", "Bell pepper", "Belt", "Bench", "Bicycle", "Bicycle helmet", "Bicycle wheel", "Bidet", "Billboard", "Billiard table", "Binoculars", "Bird", "Blender", "Blue jay", "Boat", "Bomb", "Book", "Bookcase", "Boot", "Bottle", "Bottle opener", "Bow and arrow", "Bowl", "Bowling equipment", "Box", "Boy", "Brassiere", "Bread", "Briefcase", "Broccoli", "Bronze sculpture", "Brown bear", "Building", "Bull", "Burrito", "Bus", "Bust", "Butterfly", "Cabbage", "Cabinetry", "Cake", "Cake stand", "Calculator", "Camel", "Camera", "Can opener", "Canary", "Candle", "Candy", "Cannon", "Canoe", "Cantaloupe", "Car", "Carnivore", "Carrot", "Cart", "Cassette deck", "Castle", "Cat", "Cat furniture", "Caterpillar", "Cattle", "Ceiling fan", "Cello", "Centipede", "Chainsaw", "Chair", "Cheese", "Cheetah", "Chest of drawers", "Chicken", "Chime", "Chisel", "Chopsticks", "Christmas tree", "Clock", "Closet", "Clothing", "Coat", "Cocktail", "Cocktail shaker", "Coconut", "Coffee", "Coffee cup", "Coffee table", "Coffeemaker", "Coin", "Common fig", "Common sunflower", "Computer keyboard", "Computer monitor", "Computer mouse", "Container", "Convenience store", "Cookie", "Cooking spray", "Corded phone", "Cosmetics", "Couch", "Countertop", "Cowboy hat", "Crab", "Cream", "Cricket ball", "Crocodile", "Croissant", "Crown", "Crutch", "Cucumber", "Cupboard", "Curtain", "Cutting board", "Dagger", "Dairy Product", "Deer", "Desk", "Dessert", "Diaper", "Dice", "Digital clock", "Dinosaur", "Dishwasher", "Dog", "Dog bed", "Doll", "Dolphin", "Door", "Door handle", "Doughnut", "Dragonfly", "Drawer", "Dress", "Drill (Tool)", "Drink", "Drinking straw", "Drum", "Duck", "Dumbbell", "Eagle", "Earrings", "Egg (Food)", "Elephant", "Envelope", "Eraser", "Face powder", "Facial tissue holder", "Falcon", "Fashion accessory", "Fast food", "Fax", "Fedora", "Filing cabinet", "Fire hydrant", "Fireplace", "Fish", "Flag", "Flashlight", "Flower", "Flowerpot", "Flute", "Flying disc", "Food", "Food processor", "Football", "Football helmet", "Footwear", "Fork", "Fountain", "Fox", "French fries", "French horn", "Frog", "Fruit", "Frying pan", "Furniture", "Garden Asparagus", "Gas stove", "Giraffe", "Girl", "Glasses", "Glove", "Goat", "Goggles", "Goldfish", "Golf ball", "Golf cart", "Gondola", "Goose", "Grape", "Grapefruit", "Grinder", "Guacamole", "Guitar", "Hair dryer", "Hair spray", "Hamburger", "Hammer", "Hamster", "Hand dryer", "Handbag", "Handgun", "Harbor seal", "Harmonica", "Harp", "Harpsichord", "Hat", "Headphones", "Heater", "Hedgehog", "Helicopter", "Helmet", "High heels", "Hiking equipment", "Hippopotamus", "Home appliance", "Honeycomb", "Horizontal bar", "Horse", "Hot dog", "House", "Houseplant", "Human arm", "Human beard", "Human body", "Human ear", "Human eye", "Human face", "Human foot", "Human hair", "Human hand", "Human head", "Human leg", "Human mouth", "Human nose", "Humidifier", "Ice cream", "Indoor rower", "Infant bed", "Insect", "Invertebrate", "Ipod", "Isopod", "Jacket", "Jacuzzi", "Jaguar (Animal)", "Jeans", "Jellyfish", "Jet ski", "Jug", "Juice", "Kangaroo", "Kettle", "Kitchen & dining room table", "Kitchen appliance", "Kitchen knife", "Kitchen utensil", "Kitchenware", "Kite", "Knife", "Koala", "Ladder", "Ladle", "Ladybug", "Lamp", "Land vehicle", "Lantern", "Laptop", "Lavender (Plant)", "Lemon", "Leopard", "Light bulb", "Light switch", "Lighthouse", "Lily", "Limousine", "Lion", "Lipstick", "Lizard", "Lobster", "Loveseat", "Luggage and bags", "Lynx", "Magpie", "Mammal", "Man", "Mango", "Maple", "Maracas", "Marine invertebrates", "Marine mammal", "Measuring cup", "Mechanical fan", "Medical equipment", "Microphone", "Microwave oven", "Milk", "Miniskirt", "Mirror", "Missile", "Mixer", "Mixing bowl", "Mobile phone", "Monkey", "Moths and butterflies", "Motorcycle", "Mouse", "Muffin", "Mug", "Mule", "Mushroom", "Musical instrument", "Musical keyboard", "Nail (Construction)", "Necklace", "Nightstand", "Oboe", "Office building", "Office supplies", "Orange", "Organ (Musical Instrument)", "Ostrich", "Otter", "Oven", "Owl", "Oyster", "Paddle", "Palm tree", "Pancake", "Panda", "Paper cutter", "Paper towel", "Parachute", "Parking meter", "Parrot", "Pasta", "Pastry", "Peach", "Pear", "Pen", "Pencil case", "Pencil sharpener", "Penguin", "Perfume", "Person", "Personal care", "Personal flotation device", "Piano", "Picnic basket", "Picture frame", "Pig", "Pillow", "Pineapple", "Pitcher (Container)", "Pizza", "Pizza cutter", "Plant", "Plastic bag", "Plate", "Platter", "Plumbing fixture", "Polar bear", "Pomegranate", "Popcorn", "Porch", "Porcupine", "Poster", "Potato", "Power plugs and sockets", "Pressure cooker", "Pretzel", "Printer", "Pumpkin", "Punching bag", "Rabbit", "Raccoon", "Racket", "Radish", "Ratchet (Device)", "Raven", "Rays and skates", "Red panda", "Refrigerator", "Remote control", "Reptile", "Rhinoceros", "Rifle", "Ring binder", "Rocket", "Roller skates", "Rose", "Rugby ball", "Ruler", "Salad", "Salt and pepper shakers", "Sandal", "Sandwich", "Saucer", "Saxophone", "Scale", "Scarf", "Scissors", "Scoreboard", "Scorpion", "Screwdriver", "Sculpture", "Sea lion", "Sea turtle", "Seafood", "Seahorse", "Seat belt", "Segway", "Serving tray", "Sewing machine", "Shark", "Sheep", "Shelf", "Shellfish", "Shirt", "Shorts", "Shotgun", "Shower", "Shrimp", "Sink", "Skateboard", "Ski", "Skirt", "Skull", "Skunk", "Skyscraper", "Slow cooker", "Snack", "Snail", "Snake", "Snowboard", "Snowman", "Snowmobile", "Snowplow", "Soap dispenser", "Sock", "Sofa bed", "Sombrero", "Sparrow", "Spatula", "Spice rack", "Spider", "Spoon", "Sports equipment", "Sports uniform", "Squash (Plant)", "Squid", "Squirrel", "Stairs", "Stapler", "Starfish", "Stationary bicycle", "Stethoscope", "Stool", "Stop sign", "Strawberry", "Street light", "Stretcher", "Studio couch", "Submarine", "Submarine sandwich", "Suit", "Suitcase", "Sun hat", "Sunglasses", "Surfboard", "Sushi", "Swan", "Swim cap", "Swimming pool", "Swimwear", "Sword", "Syringe", "Table", "Table tennis racket", "Tablet computer", "Tableware", "Taco", "Tank", "Tap", "Tart", "Taxi", "Tea", "Teapot", "Teddy bear", "Telephone", "Television", "Tennis ball", "Tennis racket", "Tent", "Tiara", "Tick", "Tie", "Tiger", "Tin can", "Tire", "Toaster", "Toilet", "Toilet paper", "Tomato", "Tool", "Toothbrush", "Torch", "Tortoise", "Towel", "Tower", "Toy", "Traffic light", "Traffic sign", "Train", "Training bench", "Treadmill", "Tree", "Tree house", "Tripod", "Trombone", "Trousers", "Truck", "Trumpet", "Turkey", "Turtle", "Umbrella", "Unicycle", "Van", "Vase", "Vegetable", "Vehicle", "Vehicle registration plate", "Violin", "Volleyball (Ball)", "Waffle", "Waffle iron", "Wall clock", "Wardrobe", "Washing machine", "Waste container", "Watch", "Watercraft", "Watermelon", "Weapon", "Whale", "Wheel", "Wheelchair", "Whisk", "Whiteboard", "Willow", "Window", "Window blind", "Wine", "Wine glass", "Wine rack", "Winter melon", "Wok", "Woman", "Wood-burning stove", "Woodpecker", "Worm", "Wrench", "Zebra", "Zucchini"],
  color: ["None", "red", "orange", "yellow", "green", "blue", "purple", "black", "white", "pink", "brown", "gray", "light green", "silver", "gold", "orange-red", "turquoise", "dark brown", "moss green", "dark orange", "light blue", "burgundy", "cream", "tomato red", "violet", "navy blue", "sky blue", "deep pink", "forest green", "fire red", "sea blue"]
}

function showDropdown(input) {
  const list = input.nextElementSibling;
  list.innerHTML = '';
  const values = data[input.name];
  const inputValue = input.value.toLowerCase();

  const filteredValues = values.filter(value =>
    value.toLowerCase().includes(inputValue)
  );

  filteredValues.forEach(value => {
    const listItem = document.createElement('li');
    listItem.textContent = value;
    listItem.onclick = function () {
      input.value = this.textContent;
      list.style.display = 'none';
    };
    list.appendChild(listItem);
  });

  if (filteredValues.length > 0) {
    list.style.display = 'block';
  } else {
    list.style.display = 'none';
  }

  document.addEventListener('click', function (e) {
    if (e.target !== input) {
      list.style.display = 'none';
    }
    if (!values.includes(input.value)) {
      input.value = '';
    }
  });
}

clear.addEventListener('click', () => {
  FormObject.innerHTML = '';
})

function getTags() {
  const rowItems = document.querySelectorAll('.row-item');
  const result = [];
  rowItems.forEach(rowItem => {
    const inputs = rowItem.querySelectorAll('input[type="text"]');
    const values = Array.from(inputs).map(input => input.value.replace(" ", "+")).join(' ');
    result.push(values);
  });
  return result;
}
//help button and image interactions
const helpButton = document.getElementById('helpButton');
const modalBox = document.getElementById('modalBox');
const closeButton = document.getElementById('closeButton');
const slide1 = document.querySelector('.slide-1');
const slide2 = document.querySelector('.slide-2');
const slide3 = document.querySelector('.slide-3');
const overlay = document.getElementById('overlay');
const carouselimg = document.querySelectorAll(".carousel-image");
const IRBtn = document.querySelectorAll('.IR_Btn');

function getYouTubeVideoId(url) {
  if (url) {
    const regex = /[?&]v=([^&#]*)/;
    const match = url.match(regex);
    return match ? match[1] : null;
  }
  return null;
}

function hideSlide() {
  slide3.style.display = 'none';
  slide2.style.display = 'none';
  slide1.style.display = 'none';
}

function showModal(src, id) {
  hideSlide();
  modalBox.style.display = 'block';
  overlay.style.display = 'block';
  slide2.style.display = 'block';

  const imgpath = src.split("/");
  const videopath = imgpath[imgpath.length - 2];
  fetch(`../data/metadata/${videopath}.json`)
    .then(response => response.json())
    .then((metadata) => {
      const video_url = metadata['watch_url'];
      const videoId = getYouTubeVideoId(video_url);
      const frameId = imgpath[imgpath.length - 1].replace("frame_", "").replace(".webp", "").replace(".png", "").replace("key", "");
      fetch("../data/index/fps.json")
        .then(response => response.json())
        .then((fpsdata) => {
          seconds = frameId / fpsdata[videopath];
          const fps = fpsdata[videopath];

          slide2.innerHTML = `
        <div style="max-height: 80vh; overflow-y: auto; padding-right: 10px;">
          <h2>Frame information</h2>
          <p><b>url</b>: <a target="_blank" href="https://www.youtube.com/watch?v=${videoId}&t=${Math.floor(seconds)}s">
            https://www.youtube.com/watch?v=${videoId}&t=${Math.floor(seconds)}s<a><br>
            <b>Video_id</b>: ${videopath}<br>
            <b>Initial keyframe</b>: ${frameId}<br>
            <b>fps</b>: ${fps}<br>
            <b>Current timestamp</b>: <span id="currentTimestamp" style="color: #007bff; font-weight: bold;">0 ms</span><br>
            <b>Current frame</b>: <span id="currentFrame" style="color: #007bff; font-weight: bold;">0</span>
          </p>
          <button id="submitBtn" style="margin: 10px 0; padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
            🚀 Submit to DRES
          </button>
          <div id="submitStatus" style="margin-top: 10px; padding: 10px; border-radius: 4px; display: none;"></div>
          <iframe id="videoIframe" width="100%" height="315" 
          src="https://www.youtube.com/embed/${videoId}?start=${Math.floor(seconds)}&enablejsapi=1&autoplay=1&rel=0" 
          title="YouTube video player" frameborder="0" loading="lazy" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
          <div id="debugPanel" style="margin-top: 15px; padding: 12px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; display: none;">
            <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #495057;">🐛 Submission Debug Info</h4>
            <div style="font-family: monospace; font-size: 12px; line-height: 1.6;">
              <div><strong>Task:</strong> <span id="debugTask" style="color: #007bff;"></span></div>
              <div><strong>Video ID:</strong> <span id="debugVideoId"></span></div>
              <div><strong>Frame submitted:</strong> <span id="debugFrame" style="color: #28a745;"></span></div>
              <div><strong>Timestamp (ms):</strong> <span id="debugMs" style="color: #28a745;"></span></div>
              <div><strong>FPS:</strong> <span id="debugFps"></span></div>
              <div style="margin-top: 8px;"><strong>JSON Payload:</strong></div>
              <pre id="debugJson" style="background: #343a40; color: #f8f9fa; padding: 8px; border-radius: 4px; overflow-x: auto; margin: 5px 0 0 0;"></pre>
            </div>
          </div>
        </div>`;

          // Setup YouTube Player API
          let player;
          let currentTimeMs = Math.floor(seconds * 1000);
          let currentFrameNum = frameId;

          const currentTimestampEl = document.getElementById('currentTimestamp');
          const currentFrameEl = document.getElementById('currentFrame');

          // Update display
          function updateTimeDisplay() {
            if (player && player.getCurrentTime) {
              const timeInSeconds = player.getCurrentTime();
              currentTimeMs = Math.floor(timeInSeconds * 1000);
              currentFrameNum = Math.floor(timeInSeconds * fps);

              currentTimestampEl.textContent = currentTimeMs + ' ms';
              currentFrameEl.textContent = currentFrameNum;
            }
          }

          // Initialize YouTube Player
          function onYouTubeIframeAPIReady() {
            const iframe = document.getElementById('videoIframe');
            player = new YT.Player(iframe, {
              events: {
                'onReady': function () {
                  // Update time every 200ms
                  setInterval(updateTimeDisplay, 200);
                },
                'onStateChange': function (event) {
                  if (event.data === YT.PlayerState.PAUSED || event.data === YT.PlayerState.PLAYING) {
                    updateTimeDisplay();
                  }
                }
              }
            });
          }

          // Load YouTube API if not already loaded
          if (typeof YT === 'undefined' || typeof YT.Player === 'undefined') {
            const tag = document.createElement('script');
            tag.src = 'https://www.youtube.com/iframe_api';
            const firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
            window.onYouTubeIframeAPIReady = onYouTubeIframeAPIReady;
          } else {
            onYouTubeIframeAPIReady();
          }

          // Add submit button event listener
          setTimeout(() => {
            const submitBtn = document.getElementById('submitBtn');
            const submitStatus = document.getElementById('submitStatus');
            const debugPanel = document.getElementById('debugPanel');
            const debugTask = document.getElementById('debugTask');
            const debugVideoId = document.getElementById('debugVideoId');
            const debugFrame = document.getElementById('debugFrame');
            const debugMs = document.getElementById('debugMs');
            const debugFps = document.getElementById('debugFps');
            const debugJson = document.getElementById('debugJson');

            if (submitBtn) {
              submitBtn.addEventListener('click', async () => {
                submitBtn.disabled = true;
                submitBtn.textContent = '⏳ Submitting...';
                submitStatus.style.display = 'none';
                debugPanel.style.display = 'none';

                // Get current time from player
                updateTimeDisplay();

                // Prepare submission data
                const submissionData = {
                  videoId: videopath,
                  frame: currentFrameNum,
                  fps: fps,
                  timestampMs: currentTimeMs
                };

                // Prepare DRES payload (what will be sent to competition server)
                const dresPayload = {
                  answerSets: [
                    {
                      answers: [
                        {
                          mediaItemName: videopath,
                          start: currentTimeMs,
                          end: currentTimeMs
                        }
                      ]
                    }
                  ]
                };

                // Show debug info
                debugTask.textContent = 'KIS (Known-Item Search)';
                debugVideoId.textContent = videopath;
                debugFrame.textContent = currentFrameNum;
                debugMs.textContent = currentTimeMs + ' ms';
                debugFps.textContent = fps;

                // Show both: request to our API and DRES payload
                const debugPayload = {
                  "API Request to /api/submit": submissionData,
                  "DRES Competition Payload": dresPayload
                };
                debugJson.textContent = JSON.stringify(debugPayload, null, 2);
                debugPanel.style.display = 'block';

                try {
                  const response = await fetch('/api/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(submissionData)
                  });

                  const result = await response.json();
                  
                  // DEBUG: Log full response to see what we get
                  console.log('Submit Response:', result);
                  console.log('HTTP Status:', response.status);

                  if (response.status === 200) {
                    // Get info from DRES server
                    const dresStatus = (result.status || 'UNKNOWN').toString().toUpperCase();
                    const description = (result.description || '').toLowerCase();
                    
                    console.log('DRES Status:', dresStatus);
                    console.log('Description:', result.description);
                    
                    // Determine display - PRIORITIZE description over status
                    let statusIcon = '✅';
                    let bgColor = '#d4edda';
                    let textColor = '#155724';
                    let statusText = dresStatus;
                    
                    // FIRST: Check description for keywords (most reliable)
                    if (description.includes('wrong') || description.includes('incorrect') || description.includes('error')) {
                      statusIcon = '❌';
                      bgColor = '#f8d7da';
                      textColor = '#721c24';
                      statusText = '❌ SAI';
                    } else if (description.includes('correct') && !description.includes('incorrect')) {
                      statusIcon = '🎉';
                      bgColor = '#d4edda';
                      textColor = '#155724';
                      statusText = '✅ ĐÚNG';
                    } 
                    // SECOND: Check DRES status field
                    else if (dresStatus === 'CORRECT') {
                      statusIcon = '🎉';
                      bgColor = '#d4edda';
                      textColor = '#155724';
                      statusText = '✅ ĐÚNG';
                    } else if (dresStatus === 'WRONG') {
                      statusIcon = '❌';
                      bgColor = '#f8d7da';
                      textColor = '#721c24';
                      statusText = '❌ SAI';
                    } else if (dresStatus === 'INDETERMINATE') {
                      statusIcon = '❓';
                      bgColor = '#fff3cd';
                      textColor = '#856404';
                      statusText = '❓ KHÔNG XÁC ĐỊNH';
                    } else if (dresStatus === 'PENDING') {
                      statusIcon = '⏳';
                      bgColor = '#e7f3ff';
                      textColor = '#004085';
                      statusText = '⏳ ĐANG CHỜ KẾT QUẢ';
                    } else if (dresStatus === 'FALSE') {
                      statusIcon = '❌';
                      bgColor = '#f8d7da';
                      textColor = '#721c24';
                      statusText = '❌ SAI';
                    } else if (dresStatus === 'TRUE') {
                      statusIcon = '🎉';
                      bgColor = '#d4edda';
                      textColor = '#155724';
                      statusText = '✅ ĐÚNG';
                    } else {
                      // Unknown - use neutral
                      statusIcon = '📝';
                      bgColor = '#e2e3e5';
                      textColor = '#383d41';
                      statusText = '📝 Status: ' + dresStatus;
                    }
                    
                    submitStatus.style.display = 'block';
                    submitStatus.style.background = bgColor;
                    submitStatus.style.color = textColor;
                    submitStatus.innerHTML = '<strong>' + statusText + '</strong><br>' +
                                           'Frame ' + currentFrameNum + ' (' + currentTimeMs + 'ms)' + 
                                           (result.description ? '<br><small>' + result.description + '</small>' : '');

                    // Update debug with response
                    debugJson.textContent += '\n\n// Server Response:\n' + JSON.stringify(result, null, 2);
                  } else {
                    throw new Error(result.error || result.description || 'Unknown error');
                  }
                } catch (error) {
                  submitStatus.style.display = 'block';
                  submitStatus.style.background = '#f8d7da';
                  submitStatus.style.color = '#721c24';
                  submitStatus.textContent = '❌ Error: ' + error.message;
                } finally {
                  submitBtn.disabled = false;
                  submitBtn.textContent = '🚀 Submit to DRES';
                }
              });
            }
          }, 100);
        })
    });
}

IRBtn.forEach(btn => {
  btn.addEventListener("click", function () {
    let url = '';
    url = new URL('/img', window.location.origin);
    url.searchParams.set('faiss', faissChoose.value);
    url.searchParams.set('page', 1);
    url.searchParams.set('imgid', this.getAttribute('data'));
    newwindow = window.open(url.toString(), '_blank');
  })
})

// Đảm bảo sự kiện click trên ảnh hoạt động
document.addEventListener('DOMContentLoaded', function () {
  const carouselImages = document.querySelectorAll(".carousel-image");
  carouselImages.forEach(img => {
    img.addEventListener("click", function () {
      showModal(this.src, this.getAttribute("data"));
    });
    // Đảm bảo hình ảnh có thể tương tác
    img.style.position = "relative";
    img.style.zIndex = "2";
    img.style.cursor = "pointer";
  });
});

helpButton.addEventListener('click', () => {
  hideSlide();
  modalBox.style.display = 'block';
  overlay.style.display = 'block';
  slide1.style.display = 'block';
});

closeButton.addEventListener('click', () => {
  modalBox.style.display = 'none';
  overlay.style.display = 'none';
  const videoIframe = document.getElementById("videoIframe");
  if (videoIframe) {
    videoIframe.src = '';
  }
});

overlay.addEventListener('click', () => {
  modalBox.style.display = 'none';
  overlay.style.display = 'none';
  const videoIframe = document.getElementById("videoIframe");
  if (videoIframe) {
    videoIframe.src = '';
  }
});

function cycleOptions() {
  let currentIndex = faissChoose.selectedIndex;
  let totalOptions = faissChoose.options.length;
  faissChoose.selectedIndex = (currentIndex + 1) % totalOptions;
}
function cycleOptionsUp() {
  let currentIndex = faissChoose.selectedIndex;
  let totalOptions = faissChoose.options.length;
  faissChoose.selectedIndex = (currentIndex - 1 + totalOptions) % totalOptions;
}


// Shortcut 
document.addEventListener("keydown", function (event) {
  if (event.key === "3" && event.ctrlKey) {
    event.preventDefault();
    document.getElementById("text").click();
    clipcheck = document.getElementById("Clip");
    handleCheckboxChange(clipcheck);
    clipcheck.checked = true;
    document.getElementById("textInput").focus();
  }
  if (event.key === "4" && event.ctrlKey) {
    event.preventDefault();
    document.getElementById("text").click();
    ICcheck = document.getElementById("IC");
    handleCheckboxChange(ICcheck);
    ICcheck.checked = true;
    document.getElementById("textInput").focus();
  }
  if (event.key === "5" && event.ctrlKey) {
    event.preventDefault();
    document.getElementById("object").click();
  }
  if (event.ctrlKey && event.key === 'ArrowRight') {
    event.preventDefault();
    nextpage.click();
  }
  if (event.ctrlKey && event.key === 'ArrowDown') {
    event.preventDefault();
    cycleOptions();
  }
  if (event.ctrlKey && event.key === 'ArrowLeft') {
    event.preventDefault();
    prevpage.click();
  }
  if (event.ctrlKey && event.key === 'ArrowUp') {
    event.preventDefault();
    cycleOptionsUp();
  }
  if (event.key === " " && event.ctrlKey) {
    event.preventDefault();
    addBtn.click();
  }
  if (event.key === "Enter" && event.ctrlKey) {
    event.preventDefault();
    searchBtn.forEach(btn => {
      btn.click();
    });
  }
});
// Image Search Functionality
let selectedImageFile = null;

// Handle file input
document.getElementById('imageFileInput').addEventListener('change', function(e) {
  const file = e.target.files[0];
  if (file && file.type.startsWith('image/')) {
    selectedImageFile = file;
    displayImagePreview(file);
  }
});

// Handle paste
document.getElementById('imagePasteArea').addEventListener('paste', function(e) {
  e.preventDefault();
  const items = e.clipboardData.items;
  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1) {
      const file = items[i].getAsFile();
      selectedImageFile = file;
      displayImagePreview(file);
      break;
    }
  }
});

// Handle drag and drop
const pasteArea = document.getElementById('imagePasteArea');
pasteArea.addEventListener('dragover', function(e) {
  e.preventDefault();
  this.style.borderColor = '#007bff';
});

pasteArea.addEventListener('dragleave', function(e) {
  e.preventDefault();
  this.style.borderColor = '#ccc';
});

pasteArea.addEventListener('drop', function(e) {
  e.preventDefault();
  this.style.borderColor = '#ccc';
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    selectedImageFile = file;
    displayImagePreview(file);
  }
});

// Display image preview
function displayImagePreview(file) {
  const reader = new FileReader();
  reader.onload = function(e) {
    const preview = document.getElementById('imagePreview');
    preview.src = e.target.result;
    preview.style.display = 'block';
  };
  reader.readAsDataURL(file);
}

// Modify search button to handle image search
const originalSearchBtnHandler = document.querySelector('.search_btn');
if (originalSearchBtnHandler) {
  originalSearchBtnHandler.addEventListener('click', async function(e) {
    // Check if image search is active
    const imageSearchActive = document.getElementById('imageSearchInput').style.display !== 'none';
    
    if (imageSearchActive && selectedImageFile) {
      e.preventDefault();
      e.stopPropagation();
      
      // Create a form and submit it directly (browser will navigate to result)
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/clip/image_search';
      form.enctype = 'multipart/form-data';
      
      // Add hidden input for faiss model
      const faissInput = document.createElement('input');
      faissInput.type = 'hidden';
      faissInput.name = 'faiss';
      faissInput.value = document.getElementById('faiss-select').value;
      form.appendChild(faissInput);
      
      // Add file input with the selected file
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.name = 'image';
      fileInput.style.display = 'none';
      
      // Create a DataTransfer to set the file
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(selectedImageFile);
      fileInput.files = dataTransfer.files;
      
      form.appendChild(fileInput);
      
      // Append form to body and submit
      document.body.appendChild(form);
      form.submit();
      
      return false;
    }
  });
}
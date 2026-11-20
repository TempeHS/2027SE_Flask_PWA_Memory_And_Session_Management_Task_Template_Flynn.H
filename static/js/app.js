/**
 * Client-side code that runs on every page of the canteen app.
 * README Steps 8 and 9 change this file.
 */

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/serviceWorker.js");
}

const MAX_ACTIVITY_ITEMS = 5;

/**
 * Add a message to the top of the "Live updates" list on the menu page.
 * README Step 8 limits how many messages are kept.
 */
function addActivity(message) {
  const feed = document.getElementById("activity");
  if (!feed) return;
  const item = document.createElement("li");
  item.className = "list-group-item small";
  item.textContent = message;
  feed.prepend(item);
  while (feed.children.length > MAX_ACTIVITY_ITEMS) {
    feed.lastElementChild.remove();
  }
}
/**
 * Ask the server for this user's order and update the page to match.
 * It runs every 2 seconds, so every open tab shows the same order.
 * README Step 9 changes how the order is requested and saved.
 */
async function refreshMyOrder() {
  try {
    const response = await fetch("/my-order.json", { cache: "no-store" });
    const myOrder = await response.json();
    const total = (myOrder.total / 100).toFixed(2);
    document.getElementById("order-count").textContent = myOrder.count;
    localStorage.setItem("myOrder", JSON.stringify(myOrder));
    addActivity(
      `${new Date().toLocaleTimeString()}: ${myOrder.count} items, $${total}`,
    );
  } catch (error) {
    const saved = JSON.parse(localStorage.getItem("myOrder"));
    addActivity(
      `Offline: your last saved order had ${saved ? saved.count : 0} items`,
    );
  }
}
if (document.getElementById("order-count")) {
  refreshMyOrder();
  setInterval(refreshMyOrder, 2000);
}

document.getElementById('searchBtn').addEventListener('click', async () => {
  const name = document.getElementById('charName').value.trim().toLowerCase(); // normalize input
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';

  if (!name) {
    resultsDiv.textContent = 'Please enter a character name.';
    return;
  }

  try {
    // Fetch and preview index.json
    const indexRes = await fetch('index.json');
    const indexText = await indexRes.text(); // raw text preview
//    console.log("Fetched text:", indexText.slice(0, 200));
    const index = JSON.parse(indexText); // parsed object
//    console.log("Parsed JSON:", index);

    // normalize keys of index.json once
    const normalizedIndex = {};
    for (const key in index) {
      normalizedIndex[key.toLowerCase()] = index[key];
    }

    const dates = normalizedIndex[name];
    if (!dates) {
      resultsDiv.textContent = `No snapshots found for "${name}".`;
      return;
    }

    // Fetch all snapshot files that contain this character
    const allData = [];
    for (const date of dates) {
      const snapRes = await fetch(`snapshots/${date}.json`);
      const snap = await snapRes.json();

      // normalize snapshot keys too
      const normalizedSnap = {};
      for (const key in snap) {
        normalizedSnap[key.toLowerCase()] = snap[key];
      }

      if (normalizedSnap[name]) {
        allData.push(normalizedSnap[name]);
      }
    }

    // Build table
    let html = `Snapshots via build planner for <a href="https://beta.pathofdiablo.com/armory?name=${name}" target="_blank">${name}</a><br><br><table><tr><th>Date/Time</th><th>Build Planner URL</th></tr>`;
    for (const entry of allData) {
      html += `<tr><td>${entry.timestamp || ""}</td><td><a href="${entry.url}" target="_blank">${entry.url}</a></td></tr>`;
    }
    html += '</table>';

    resultsDiv.innerHTML = html;

  } catch (err) {
    console.error(err);
    resultsDiv.textContent = 'Error fetching snapshots.';
  }
});

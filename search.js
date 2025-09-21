document.getElementById('searchBtn').addEventListener('click', async () => {
  const name = document.getElementById('charName').value.trim();
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';

  if (!name) {
    resultsDiv.textContent = 'Please enter a character name.';
    return;
  }

  try {
    // Normalize name → lowercase filename
    const fileName = name.toLowerCase();
    const res = await fetch(`snapshots/${fileName}.json`);

    if (!res.ok) {
      resultsDiv.textContent = `No history found for "${name}".`;
      return;
    }

    const history = await res.json(); // should be an array of {url, timestamp}

    if (!Array.isArray(history) || history.length === 0) {
      resultsDiv.textContent = `No history found for "${name}".`;
      return;
    }

    // Build table
    let html = `Snapshots via build planner for <a href="https://beta.pathofdiablo.com/armory?name=${encodeURIComponent(name)}" target="_blank">${name}</a><br><br><table><tr><th>Date/Time</th><th>Build Planner URL</th></tr>`;
    for (const entry of history) {
      html += `<tr><td>${entry.timestamp || ""}</td><td><a href="${entry.url}" target="_blank">${entry.url}</a></td></tr>`;
    }
    html += '</table>';

    resultsDiv.innerHTML = html;

  } catch (err) {
    console.error(err);
    resultsDiv.textContent = 'Error fetching character history.';
  }
});

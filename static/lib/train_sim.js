/**
 * train_sim.js — Real-Time Track-Following Train Simulation Engine
 * SAMANVAY Railway DSS
 *
 * Key Architecture:
 * 1. Tracks follow EXACT drawn corridor polylines from /api/network (0 meters off-track).
 * 2. Computes true curved track distances (Haversine) across all intermediate stations.
 * 3. Calculates physical train speed: Speed = Track Distance / Block Time.
 * 4. Places trains at exact kilometer distance along the track at the current time.
 * 5. Separates Up and Down trains onto dual parallel tracks (eliminates stacking/clusters).
 * 6. Displays both Train Number AND Train Name on the marker label and popup.
 * 7. Interactive simulation time controls (Live IST, Rush hour presets, Custom time).
 */

(function (global) {
  "use strict";

  const TICK_MS = 3000;
  const REFRESH_DATA_MS = 5 * 60 * 1000;

  // Corridor color palette (matches map.html)
  const CORRIDOR_COLORS = {
    hwh_bwn_main:      "#06b6d4",   // Cyan
    hwh_bwn_chord:     "#f97316",   // Orange
    bly_bwn_asn_trunk: "#f59e0b",   // Amber
    bwn_asn_trunk:     "#f59e0b",   // Amber
    hwh_bwn_asn_line:  "#38bdf8",   // Sky Blue
    sdah_knj_line:     "#a855f7",   // Purple
    hwh_skg_line:      "#22c55e",   // Emerald Green
    hwh_sgkh_line:     "#22c55e",   // Green
  };

  const CORRIDOR_NAMES = {
    hwh_bwn_main:      "Howrah – Barddhaman Main Line",
    hwh_bwn_chord:     "Howrah – Barddhaman Chord Line",
    bly_bwn_asn_trunk: "Bally – Barddhaman – Asansol Trunk",
    bwn_asn_trunk:     "Barddhaman – Asansol Trunk",
    hwh_bwn_asn_line:  "Howrah – Barddhaman – Asansol Line",
    sdah_knj_line:     "Sealdah – Krishnanagar City Line",
    hwh_skg_line:      "Howrah – Saktigarh Line",
    hwh_sgkh_line:     "Howrah – Saktigarh Line",
  };

  // ── Math & Geometry Helpers ──────────────────────────────────────────────────

  function haversineKm(p1, p2) {
    const R = 6371.0;
    const lat1 = (p1[0] * Math.PI) / 180;
    const lon1 = (p1[1] * Math.PI) / 180;
    const lat2 = (p2[0] * Math.PI) / 180;
    const lon2 = (p2[1] * Math.PI) / 180;
    const dlat = lat2 - lat1;
    const dlon = lon2 - lon1;
    const a =
      Math.sin(dlat / 2) ** 2 +
      Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function normalizeDay(d) {
    if (!d) return "";
    const s = String(d).trim().toLowerCase();
    const map = {
      monday: "mon", tuesday: "tue", wednesday: "wed",
      thursday: "thu", friday: "fri", saturday: "sat", sunday: "sun",
      mon: "mon", tue: "tue", wed: "wed", thu: "thu", fri: "fri", sat: "sat", sun: "sun"
    };
    return map[s] || s.slice(0, 3);
  }

  function getNowMinutes() {
    const override = global.SAMANVAY_SIM_TIME;
    if (override && /^\d{1,2}:\d{2}$/.test(override.trim())) {
      const [h, m] = override.trim().split(":").map(Number);
      return (h * 60 + m) % 1440;
    }
    const now = new Date();
    const istMs = now.getTime() + (5.5 * 60 * 60 * 1000);
    const ist = new Date(istMs);
    return ist.getUTCHours() * 60 + ist.getUTCMinutes() + (ist.getUTCSeconds() / 60);
  }

  function getTodayDay() {
    const override = global.SAMANVAY_SIM_DAY;
    if (override && typeof override === "string" && override.trim()) {
      return normalizeDay(override.trim());
    }
    const now = new Date();
    const istMs = now.getTime() + (5.5 * 60 * 60 * 1000);
    const dayNames = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
    return dayNames[new Date(istMs).getUTCDay()];
  }

  function parseHHMM(s) {
    if (!s || s === "None" || s === "--" || s === "N/A") return null;
    const parts = String(s).trim().split(":");
    if (parts.length < 2) return null;
    const h = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    if (isNaN(h) || isNaN(m)) return null;
    return (h * 60 + m) % 1440;
  }

  function formatHHMM(mins) {
    mins = ((mins % 1440) + 1440) % 1440;
    const h = Math.floor(mins / 60).toString().padStart(2, "0");
    const m = (mins % 60).toString().padStart(2, "0");
    return `${h}:${m}`;
  }

  function cleanTrainName(name, num) {
    if (!name || name === num || name === "None") return `Exp ${num}`;
    return name
      .replace(/Special Fare/gi, "Spl")
      .replace(/Special/gi, "Spl")
      .replace(/Express/gi, "Exp")
      .replace(/Superfast/gi, "SF")
      .replace(/Local/gi, "Local")
      .trim();
  }

  // ── SVG Locomotive Icon with Train Name Badge and Direction Arrow ───────────

  function isTrainUp(trainNumber, trainName, reversed = undefined) {
    if (typeof reversed === "boolean") {
      // In TrainPathCalculator, reversed means moving towards terminal (HWH/SDAH) = DOWN
      // non-reversed means moving away from terminal (Outbound) = UP
      return !reversed;
    }
    const name = (trainName || "").toUpperCase();
    if (name.includes(" DOWN") || name.includes(" DN") || name.includes(" - HOWRAH") || name.includes(" - SEALDAH")) return false;
    if (name.includes(" UP") || name.startsWith("HOWRAH -") || name.startsWith("SEALDAH -")) return true;

    const num = parseInt(trainNumber, 10);
    if (!isNaN(num) && num > 0) {
      return (num % 2 !== 0); // In Indian Railways, odd is UP, even is DOWN
    }
    return true;
  }

  function createTrainIcon(color, trainNumber, trainName, reversed = undefined) {
    const isUp = isTrainUp(trainNumber, trainName, reversed);
    const flip = reversed ? "transform:scaleX(-1);" : "";
    const shortName = cleanTrainName(trainName, trainNumber);

    const svgHtml = `
      <div class="train-marker-wrapper" title="${trainNumber} - ${trainName} (${isUp ? 'UP Train' : 'DOWN Train'})" style="position:relative;cursor:pointer;display:flex;flex-direction:column;align-items:center;">
        <!-- Directional Locomotive SVG -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 28"
             width="48" height="22" style="${flip}filter:drop-shadow(0 2px 6px rgba(0,0,0,.95));transition:transform 0.4s ease;">
          <rect x="2" y="6" width="48" height="16" rx="4" fill="${color}" opacity="0.95"/>
          <path d="M50 6 L62 9 L62 19 L50 22 Z" fill="${color}" opacity="0.9"/>
          <rect x="7"  y="9" width="8" height="6" rx="1.5" fill="rgba(255,255,255,0.45)"/>
          <rect x="19" y="9" width="8" height="6" rx="1.5" fill="rgba(255,255,255,0.45)"/>
          <rect x="31" y="9" width="8" height="6" rx="1.5" fill="rgba(255,255,255,0.45)"/>
          <rect x="52" y="9" width="7" height="5" rx="1" fill="rgba(255,255,255,0.65)"/>
          <circle cx="14" cy="23" r="3.5" fill="#0f172a" stroke="${color}" stroke-width="1.5"/>
          <circle cx="28" cy="23" r="3.5" fill="#0f172a" stroke="${color}" stroke-width="1.5"/>
          <circle cx="42" cy="23" r="3.5" fill="#0f172a" stroke="${color}" stroke-width="1.5"/>
          <circle cx="56" cy="22" r="3" fill="#0f172a" stroke="${color}" stroke-width="1.5"/>
          <circle cx="62" cy="14" r="2.5" fill="#fef08a" opacity="0.95"/>
        </svg>

        <!-- Container with Train Name/Number Box + Arrow directly to the right/beside the box -->
        <div style="display:flex; align-items:center; gap:3.5px; margin-top:2px;">
          <!-- Box where train name and number is placed -->
          <div style="
            background:rgba(10,15,30,0.96); color:#f8fafc;
            font-size:9px; font-weight:700; padding:2px 7px; border-radius:5px;
            border:1.5px solid ${color}; white-space:nowrap; display:flex; align-items:center;
            gap:5px; box-shadow:0 3px 8px rgba(0,0,0,0.9); pointer-events:none; max-width:180px;">
            <span style="color:${color};font-family:monospace;font-weight:900;font-size:9.5px;letter-spacing:0.3px;">${trainNumber}</span>
            <span style="overflow:hidden;text-overflow:ellipsis;color:#f1f5f9;font-size:8.5px;font-weight:700;max-width:115px;">${shortName}</span>
          </div>

          <!-- Arrow beside / right of the box where train name and number is placed -->
          <div style="
            background:${isUp ? 'rgba(6,78,59,0.96)' : 'rgba(136,19,55,0.96)'};
            color:${isUp ? '#34d399' : '#fb7185'};
            border:1.5px solid ${isUp ? '#10b981' : '#f43f5e'};
            box-shadow:0 3px 8px rgba(0,0,0,0.9);
            border-radius:4px; padding:1.5px 5px; font-size:9px; font-weight:900;
            display:flex; align-items:center; gap:2px; white-space:nowrap; pointer-events:none;"
            title="${isUp ? 'UP Direction Train (Outbound)' : 'DOWN Direction Train (Inbound)'}">
            <span style="font-size:12px; line-height:1; font-weight:900;">${isUp ? '⬆' : '⬇'}</span>
            <span style="font-size:8.5px; letter-spacing:0.4px; font-weight:900;">${isUp ? 'UP' : 'DN'}</span>
          </div>
        </div>
      </div>`;

    return L.divIcon({
      html: svgHtml,
      className: "train-svg-icon",
      iconSize:   [250, 46],
      iconAnchor: [125, 16],
      popupAnchor:[0, -20],
    });
  }

  // ── Simulator Core ──────────────────────────────────────────────────────────

  class TrainSimulator {
    constructor(map) {
      this.map = map;
      this.markers = {};
      this.trains = [];
      this.corridorTracks = {}; // corridor_id -> { coords, dists, totalKm, stations }
      this.layerGroup = L.layerGroup().addTo(map);
      this.tickTimer = null;
      this.refreshTimer = null;
      this.running = false;
    }

    async init() {
      await this._loadCorridorTracks();
      await this.loadTrains();
      this.running = true;
      this.tick();
      this.tickTimer = setInterval(() => this.tick(), TICK_MS);
      this.refreshTimer = setInterval(() => this.loadTrains(), REFRESH_DATA_MS);
      console.info("[TrainSim] Track-following simulation engine initialized");
    }

    destroy() {
      this.running = false;
      if (this.tickTimer) clearInterval(this.tickTimer);
      if (this.refreshTimer) clearInterval(this.refreshTimer);
      this.layerGroup.clearLayers();
      this.markers = {};
      console.info("[TrainSim] Engine stopped");
    }

    // ── Track Geometry Precomputation ────────────────────────────────────────

    async _loadCorridorTracks() {
      try {
        const resp = await fetch("/api/network");
        if (!resp.ok) return;
        const net = await resp.json();
        const corridors = net.primary_corridors || [];

        for (const c of corridors) {
          const coords = c.coordinates || [];
          if (coords.length < 2) continue;

          const dists = [0.0];
          for (let i = 0; i < coords.length - 1; i++) {
            dists.push(dists[dists.length - 1] + haversineKm(coords[i], coords[i + 1]));
          }

          const stations = (c.stations || []).map(s => (s.code || "").toUpperCase());
          const stationKm = {};
          const stationDetails = {};

          (c.stations || []).forEach((s, idx) => {
            const code = (s.code || "").toUpperCase();
            if (code) {
              const km = (idx < dists.length) ? dists[idx] : dists[dists.length - 1];
              stationKm[code] = km;
              stationDetails[code] = {
                code,
                name: s.name || code,
                km,
                lat: s.lat,
                long: s.long,
                index: idx
              };
            }
          });

          this.corridorTracks[c.id] = {
            id: c.id,
            name: c.name || c.id,
            coords,
            dists,
            totalKm: dists[dists.length - 1],
            stations,
            stationKm,
            stationDetails,
          };
        }

        console.info(`[TrainSim] Precomputed track geometry for ${Object.keys(this.corridorTracks).length} corridors:`,
          Object.fromEntries(Object.entries(this.corridorTracks).map(([k, v]) => [k, `${v.totalKm.toFixed(1)} km (${v.coords.length} pts)`])));
      } catch (e) {
        console.warn("[TrainSim] Failed to load corridor tracks:", e);
      }
    }

    async loadTrains() {
      try {
        const resp = await fetch("/api/real-trains");
        if (!resp.ok) return;
        const data = await resp.json();
        if (data.trains && data.trains.length > 0) {
          this.trains = data.trains;
          console.info(`[TrainSim] Loaded ${this.trains.length} corridor trains from DB cache`);
        }
      } catch (e) {
        console.warn("[TrainSim] Failed loading trains:", e);
      }
    }

    // ── Track Polyline Matcher ───────────────────────────────────────────────

    _selectTrackForTrain(train) {
      const cid = train.corridor_id;

      if (cid === "sdah_knj_line") {
        return this.corridorTracks["sdah_knj_line"];
      }

      if (cid === "bwn_asn_trunk") {
        return this.corridorTracks["bwn_asn_trunk"];
      }

      if (cid === "hwh_bwn_main") {
        return this.corridorTracks["hwh_bwn_main"];
      }

      if (cid === "hwh_skg_line") {
        // Check if train passes BDC (Bandel) -> Main Line; otherwise Chord Line
        const stops = train.corridor_stops || [];
        const hasBDC = stops.some(s => s.station_code === "BDC");
        if (hasBDC && this.corridorTracks["hwh_bwn_main"]) {
          return this.corridorTracks["hwh_bwn_main"];
        }
        // Saktigarh is connected on the Main line polyline up to index 28 (SKG)
        return this.corridorTracks["hwh_bwn_main"] || this.corridorTracks["hwh_bwn_chord"];
      }

      if (cid === "bly_bwn_asn_trunk" || cid === "hwh_bwn_asn_line") {
        // Can use Main line or Trunk line depending on where the train is
        return this.corridorTracks["hwh_bwn_main"] || this.corridorTracks["bwn_asn_trunk"];
      }

      return Object.values(this.corridorTracks)[0] || null;
    }

    // ── Exact Track Position Interpolator ────────────────────────────────────
    // Uses window.TrainPathCalculator (separate modular algorithm file)

    _computeTrackPosition(train, nowMin) {
      if (global.TrainPathCalculator) {
        const pos = global.TrainPathCalculator.calculateTrainPosition(train, nowMin, this.corridorTracks);
        if (!pos) return null;
        return {
          lat: pos.lat,
          lng: pos.lng,
          fraction: pos.fraction,
          distanceCoveredKm: pos.distanceCoveredKm,
          distanceRemainingKm: pos.distanceRemainingKm,
          totalKm: pos.totalKm,
          speedKmh: pos.speedKmh,
          avgSpeedKmh: pos.avgSpeedKmh,
          isHalted: pos.isHalted,
          haltStation: pos.haltStation,
          haltStationName: pos.haltStationName,
          startStn: pos.origin,
          startStnName: pos.originName,
          endStn: pos.destination,
          endStnName: pos.destName,
          finalDest: pos.finalDest,
          depTime: pos.depTime,
          arrTime: pos.arrTime,
          reversed: pos.reversed,
          trackId: pos.trackId,
          trackName: pos.trackName,
        };
      }

      return null;
    }

    // ── Tick — Update All Train Markers ───────────────────────────────────────

    tick() {
      if (!this.running || !this.map) return;

      const nowMin = getNowMinutes();
      const todayDay = getTodayDay();
      const activeTrainNumbers = new Set();

      for (const train of this.trains) {
        const runDays = (train.run_days || []).map(normalizeDay);
        if (runDays.length > 0 && !runDays.includes(todayDay)) continue;

        const pos = this._computeTrackPosition(train, nowMin);
        if (!pos) continue;

        const tNum = train.train_number;
        const tName = train.train_name || `Train ${tNum}`;
        activeTrainNumbers.add(tNum);
        const color = CORRIDOR_COLORS[train.corridor_id] || "#38bdf8";

        if (this.markers[tNum]) {
          const m = this.markers[tNum];
          m.setLatLng([pos.lat, pos.lng]);
          if (m._lastReversed !== pos.reversed) {
            m.setIcon(createTrainIcon(color, tNum, tName, pos.reversed));
            m._lastReversed = pos.reversed;
          }
          if (m.isPopupOpen()) {
            m.setPopupContent(this._buildPopupHTML(train, pos));
          }
        } else {
          const icon = createTrainIcon(color, tNum, tName, pos.reversed);
          const marker = L.marker([pos.lat, pos.lng], { icon, zIndexOffset: 900 })
            .bindPopup(() => this._buildPopupHTML(train, pos), { maxWidth: 340, className: "train-popup-dark" });
          marker._lastReversed = pos.reversed;
          marker.addTo(this.layerGroup);
          this.markers[tNum] = marker;
        }
      }

      // Remove trains that completed their run or aren't active at this time
      for (const tNum of Object.keys(this.markers)) {
        if (!activeTrainNumbers.has(tNum)) {
          this.layerGroup.removeLayer(this.markers[tNum]);
          delete this.markers[tNum];
        }
      }

      // Update UI Counters
      const countEl = document.getElementById("sim-train-count");
      if (countEl) countEl.textContent = activeTrainNumbers.size;

      const tabCountEl = document.getElementById("trains-tab-count");
      if (tabCountEl) tabCountEl.textContent = `${activeTrainNumbers.size} Live`;

      const timeEl = document.getElementById("sim-clock-display");
      if (timeEl) {
        const hhmm = formatHHMM(nowMin);
        const isCustom = Boolean(global.SAMANVAY_SIM_TIME);
        timeEl.textContent = `${hhmm} IST (${todayDay.toUpperCase()})${isCustom ? " [SIM]" : ""}`;
      }
    }

    _buildPopupHTML(train, pos) {
      const color = CORRIDOR_COLORS[train.corridor_id] || "#38bdf8";
      const corridorName = CORRIDOR_NAMES[train.corridor_id] || train.corridor_id;
      const pct = Math.round((pos.fraction ?? 0) * 100);
      const destLabel = pos.finalDest && pos.finalDest !== pos.endStn ? `${pos.endStn} (Final: ${pos.finalDest})` : pos.endStn;
      const isUp = isTrainUp(train.train_number, train.train_name, pos.reversed);
      const dirBadge = isUp 
        ? `<span style="font-size:10px;background:#064e3b;color:#34d399;border:1px solid #10b981;padding:2px 7px;border-radius:4px;font-weight:900;display:inline-flex;align-items:center;gap:3px;">⬆ UP TRAIN</span>`
        : `<span style="font-size:10px;background:#881337;color:#fb7185;border:1px solid #f43f5e;padding:2px 7px;border-radius:4px;font-weight:900;display:inline-flex;align-items:center;gap:3px;">⬇ DOWN TRAIN</span>`;

      const chronStops = (function() {
        const raw = train.corridor_stops || [];
        if (global.TrainPathCalculator && typeof global.TrainPathCalculator.sortStopsChronologically === "function") {
          return global.TrainPathCalculator.sortStopsChronologically(raw);
        }
        return raw;
      })();

      const stopsList = chronStops.map((s, idx) => {
        const isFirst = idx === 0;
        const isLast = idx === chronStops.length - 1;
        const arr = s.arrival && s.arrival !== "None" ? `<span style="color:#94a3b8;">▼ ${s.arrival}</span>` : "";
        const dep = s.departure && s.departure !== "None" ? `<span style="color:#38bdf8;">▲ ${s.departure}</span>` : "";
        const role = isFirst ? '<span style="font-size:8px;color:#34d399;font-weight:700;margin-left:4px;">(Origin)</span>' : (isLast ? '<span style="font-size:8px;color:#fb7185;font-weight:700;margin-left:4px;">(Terminus)</span>' : '');
        return `<tr style="border-bottom:1px solid #1e293b;">
          <td style="padding:3px 6px;color:${color};font-weight:700;">${s.station_code}${role}</td>
          <td style="padding:3px 6px;color:#cbd5e1;">${s.station_name || s.station_code}</td>
          <td style="padding:3px 6px;text-align:right;">${arr} ${dep}</td>
        </tr>`;
      }).join("");

      return `
        <div style="font-family:'Inter',system-ui,sans-serif;min-width:280px;background:#090d16;color:#e2e8f0;border-radius:8px;overflow:hidden;border:1px solid ${color}50;">
          <div style="background:${color}22;border-bottom:2px solid ${color};padding:8px 28px 8px 12px;">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;">
              <span style="font-size:14px;font-weight:800;color:${color};">🚆 ${train.train_number}</span>
              <div style="display:flex;align-items:center;gap:5px;">
                ${dirBadge}
                <span style="font-size:10px;background:#1e293b;padding:2px 6px;border-radius:4px;color:#94a3b8;font-weight:700;">${train.train_type || "EXP"}</span>
              </div>
            </div>
            <div style="font-size:12px;font-weight:700;color:#f8fafc;margin-top:2px;">${train.train_name || "Corridor Train"}</div>
            <div style="font-size:9.5px;color:#94a3b8;margin-top:2px;">${corridorName}</div>
          </div>
          <div style="padding:10px 12px;">
            <div style="background:#0f172a;border-radius:6px;padding:8px;margin-bottom:8px;border:1px solid #1e293b;">
              <div style="display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;">
                <span>${pos.isHalted ? "Station Status:" : "Current Section:"}</span>
                <span style="color:${pos.isHalted ? '#f59e0b' : color};font-weight:bold;">${pos.isHalted ? `● HALTED at ${pos.haltStationName || pos.haltStation}` : `${pos.startStn} (${pos.depTime}) ➔ ${pos.endStn} (${pos.arrTime})`}</span>
              </div>
              <div style="background:#1e293b;border-radius:3px;height:6px;margin:6px 0;overflow:hidden;">
                <div style="background:${pos.isHalted ? '#f59e0b' : color};width:${pct}%;height:100%;transition:width 0.4s ease;"></div>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:9.5px;color:#64748b;">
                <span>Dep ${pos.startStn}: <b class="text-slate-300 font-mono">${pos.depTime}</b></span>
                <span style="color:${color};font-weight:bold;">${pos.distanceCoveredKm} / ${pos.totalKm} km (${pct}%)</span>
                <span>Arr ${pos.endStn}: <b class="text-slate-300 font-mono">${pos.arrTime}</b></span>
              </div>
              <div style="display:flex;justify-content:space-between;margin-top:4px;font-size:9px;color:#94a3b8;border-top:1px solid #1e293b;padding-top:4px;">
                <span>Speed: <b style="color:#38bdf8;">${pos.isHalted ? '0 km/h (Station Halt)' : `${pos.speedKmh} km/h`}</b> <span style="color:#64748b;font-size:8.5px;">(Avg: ${pos.avgSpeedKmh || pos.speedKmh} km/h)</span></span>
                <span>Direction: <b style="color:${isUp ? '#34d399' : '#fb7185'}; font-weight:800;">${isUp ? "⬆ UP TRAIN (Outbound)" : "⬇ DOWN TRAIN (Inbound)"}</b></span>
              </div>
            </div>
            <table style="width:100%;font-size:10px;border-collapse:collapse;">
              <thead>
                <tr style="color:#64748b;text-align:left;border-bottom:1px solid #1e293b;">
                  <th style="padding:2px 6px;">Code</th>
                  <th style="padding:2px 6px;">Station</th>
                  <th style="padding:2px 6px;text-align:right;">Timing</th>
                </tr>
              </thead>
              <tbody>${stopsList}</tbody>
            </table>
            <div style="margin-top:8px;font-size:9px;color:#64748b;display:flex;justify-content:space-between;">
              <span>Days: ${(train.run_days || []).map(d => d.slice(0,3).toUpperCase()).join(" ") || "DAILY"}</span>
              <span style="color:#34d399;">● Strictly on Track Path</span>
            </div>
          </div>
        </div>
      `;
    }

    setTime(hhmm, day) {
      if (hhmm) global.SAMANVAY_SIM_TIME = hhmm;
      if (day)  global.SAMANVAY_SIM_DAY  = day;
      this.tick();
    }

    resetToLive() {
      delete global.SAMANVAY_SIM_TIME;
      delete global.SAMANVAY_SIM_DAY;
      this.tick();
    }
  }

  // ── Global Export ───────────────────────────────────────────────────────────

  let _instance = null;

  global.TrainSim = {
    init(map) {
      if (_instance) _instance.destroy();
      _instance = new TrainSimulator(map);
      return _instance.init();
    },
    destroy() {
      if (_instance) _instance.destroy();
      _instance = null;
    },
    setTime(hhmm, day) {
      if (_instance) _instance.setTime(hhmm, day);
    },
    resetToLive() {
      if (_instance) _instance.resetToLive();
    },
    getInstance() {
      return _instance;
    },
    get _instance() {
      return _instance;
    }
  };

})(window);

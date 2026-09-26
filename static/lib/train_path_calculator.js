/**
 * train_path_calculator.js — Precision Railway Track Position Algorithm
 * SAMANVAY Rail Decision Support System (DSS)
 *
 * Dedicated algorithm module for calculating real-time train positions along
 * exact GIS curved corridor track polylines and intermediate stations.
 *
 * Core Equation & Steps:
 * 1. Block Time: ΔT = T_arr - T_dep (minutes & hours, handles overnight)
 * 2. Total Track Distance: D_total (km) = Cumulative Haversine sum along drawn polyline
 * 3. Physical Speed: V = D_total / ΔT (km/h)
 * 4. Elapsed Time: t_elapsed = T_now - T_dep (minutes & hours)
 * 5. Position along track:
 *    - Distance from Origin = (t_elapsed / ΔT) * D_total (km)
 *    - Distance to Destination = D_total - Distance from Origin (km)
 * 6. Interpolation: Walk cumulative segment distances along polyline to find exact (lat, lng)
 * 7. Parallel Dual-Track Offset: ±0.00018° perpendicular shift to separate Up & Down trains
 */

(function (global) {
  "use strict";

  const EARTH_RADIUS_KM = 6371.0;

  const TrainPathCalculator = {
    // ── 1. Geometry & Haversine Math ──────────────────────────────────────────

    haversineKm(p1, p2) {
      if (!p1 || !p2) return 0;
      const lat1 = (p1[0] * Math.PI) / 180;
      const lon1 = (p1[1] * Math.PI) / 180;
      const lat2 = (p2[0] * Math.PI) / 180;
      const lon2 = (p2[1] * Math.PI) / 180;
      const dlat = lat2 - lat1;
      const dlon = lon2 - lon1;
      const a =
        Math.sin(dlat / 2) ** 2 +
        Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon / 2) ** 2;
      return EARTH_RADIUS_KM * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    },

    cumulativeDistances(coords) {
      if (!coords || coords.length < 2) return [0.0];
      const dists = [0.0];
      for (let i = 0; i < coords.length - 1; i++) {
        dists.push(dists[dists.length - 1] + this.haversineKm(coords[i], coords[i + 1]));
      }
      return dists;
    },

    interpolateAlongPolyline(coords, dists, targetKm, offsetLateralDeg = 0) {
      if (!coords || coords.length === 0) return { lat: 0, lng: 0, segIdx: 0 };
      if (coords.length === 1) return { lat: coords[0][0], lng: coords[0][1], segIdx: 0 };

      const totalKm = dists[dists.length - 1] || 0.0;
      const clampedKm = Math.max(0.0, Math.min(totalKm, targetKm));

      let segIdx = 0;
      let segAlpha = 0;
      let lat = coords[0][0];
      let lng = coords[0][1];

      for (let i = 0; i < dists.length - 1; i++) {
        if (dists[i] <= clampedKm && clampedKm <= dists[i + 1]) {
          const segDist = dists[i + 1] - dists[i];
          segAlpha = segDist > 0 ? (clampedKm - dists[i]) / segDist : 0;
          lat = coords[i][0] + (coords[i + 1][0] - coords[i][0]) * segAlpha;
          lng = coords[i][1] + (coords[i + 1][1] - coords[i][1]) * segAlpha;
          segIdx = i;
          break;
        }
      }

      // Perpendicular normal offset to render Up and Down trains on dual parallel tracks
      if (Math.abs(offsetLateralDeg) > 1e-7 && coords.length >= 2) {
        const p1 = coords[segIdx];
        const p2 = coords[Math.min(segIdx + 1, coords.length - 1)];
        const dx = p2[1] - p1[1];
        const dy = p2[0] - p1[0];
        const len = Math.sqrt(dx * dx + dy * dy) || 1.0;
        const nx = -dy / len;
        const ny = dx / len;
        lat += ny * offsetLateralDeg;
        lng += nx * offsetLateralDeg;
      }

      return { lat, lng, segIdx };
    },

    // ── 2. Time Conversion & Parsing ──────────────────────────────────────────

    parseHHMM(timeStr) {
      if (!timeStr || timeStr === "None" || timeStr === "--" || timeStr === "N/A") return null;
      const parts = String(timeStr).trim().split(":");
      if (parts.length < 2) return null;
      const h = parseInt(parts[0], 10);
      const m = parseInt(parts[1], 10);
      if (isNaN(h) || isNaN(m)) return null;
      return (h * 60 + m) % 1440;
    },

    formatHHMM(minutes) {
      const clean = ((minutes % 1440) + 1440) % 1440;
      const h = Math.floor(clean / 60).toString().padStart(2, "0");
      const m = (clean % 60).toString().padStart(2, "0");
      return `${h}:${m}`;
    },

    calculateBlockTime(depMin, arrMin) {
      if (depMin <= arrMin) {
        return arrMin - depMin;
      } else {
        // Crosses midnight
        return (arrMin + 1440) - depMin;
      }
    },

    calculateElapsedMinutes(depMin, arrMin, nowMin) {
      if (depMin <= arrMin) {
        if (depMin <= nowMin && nowMin <= arrMin) {
          return nowMin - depMin;
        }
        return null;
      } else {
        // Crosses midnight
        if (nowMin >= depMin) {
          return nowMin - depMin;
        } else if (nowMin <= arrMin) {
          return (nowMin + 1440) - depMin;
        }
        return null;
      }
    },

    // ── 3. Chronological Stop Sequence Sorting ────────────────────────────────

    getHopMinutes(t1, t2) {
      return (t2 - t1 + 1440) % 1440;
    },

    isTimeBetween(dep, arr, now) {
      if (dep <= arr) {
        return dep <= now && now <= arr;
      } else {
        // Crosses midnight (e.g. 23:40 to 01:34)
        return now >= dep || now <= arr;
      }
    },

    getElapsedMinutes(dep, arr, now) {
      if (dep <= arr) {
        return now - dep;
      } else {
        return now >= dep ? (now - dep) : (now + 1440 - dep);
      }
    },

    sortStopsChronologically(stops) {
      if (!stops || stops.length < 2) return stops || [];

      // Filter stops that have valid times
      const validStops = stops.filter(s => {
        const t = s.departure || s.arrival;
        return t && t !== "None" && t !== "--";
      });

      if (validStops.length < 2) return stops;

      const tFwd = validStops.map(s => this.parseHHMM(s.departure || s.arrival));
      if (tFwd.some(t => t === null)) return validStops;

      // Calculate total cumulative forward hop duration
      let durFwd = 0;
      for (let i = 0; i < tFwd.length - 1; i++) {
        durFwd += this.getHopMinutes(tFwd[i], tFwd[i + 1]);
      }

      // Calculate total cumulative reverse hop duration
      const tRev = [...tFwd].reverse();
      let durRev = 0;
      for (let i = 0; i < tRev.length - 1; i++) {
        durRev += this.getHopMinutes(tRev[i], tRev[i + 1]);
      }

      // The true chronological direction minimizes impossible multi-day circular hops
      if (durRev < durFwd) {
        return [...validStops].reverse();
      }

      return validStops;
    },

    // ── 4. Intelligent Corridor Track Selector ────────────────────────────────

    selectCorridorTrack(train, activeOrigin, activeDest, corridorTracks) {
      const orig = (activeOrigin || "").toUpperCase();
      const dest = (activeDest || "").toUpperCase();
      const cid = train.corridor_id;
      const stops = train.corridor_stops || [];
      const stopCodes = new Set(stops.map(s => (s.station_code || "").toUpperCase()));

      // 1. Asansol - Barddhaman Section
      if ((orig === "ASN" && dest === "BWN") || (orig === "BWN" && dest === "ASN") ||
          (stopCodes.has("ASN") && !stopCodes.has("HWH") && !stopCodes.has("BLY"))) {
        if (corridorTracks["bwn_asn_trunk"]) return corridorTracks["bwn_asn_trunk"];
      }

      // 2. Sealdah - Krishnanagar Corridor
      if (cid === "sdah_knj_line" || orig === "SDAH" || dest === "SDAH" || orig === "KNJ" || dest === "KNJ") {
        return corridorTracks["sdah_knj_line"] || Object.values(corridorTracks)[0];
      }

      // 3. Howrah - Barddhaman Main vs Chord Disambiguation
      const hasMainLineStop = stopCodes.has("BDC") || stopCodes.has("SRP") || stopCodes.has("CGR") || stopCodes.has("CNS");
      const hasChordLineStop = stopCodes.has("DKAE") || stopCodes.has("KQU") || stopCodes.has("GRAE") || stopCodes.has("MSAE");

      if (hasMainLineStop && corridorTracks["hwh_bwn_main"]) {
        return corridorTracks["hwh_bwn_main"];
      }
      if (hasChordLineStop && corridorTracks["hwh_bwn_chord"]) {
        return corridorTracks["hwh_bwn_chord"];
      }

      const tName = (train.train_name || "").toLowerCase();
      if (tName.includes("main") && corridorTracks["hwh_bwn_main"]) {
        return corridorTracks["hwh_bwn_main"];
      }

      // Default for Howrah-Saktigarh fast trains is the Chord Line
      return corridorTracks["hwh_bwn_chord"] || corridorTracks["hwh_bwn_main"] || Object.values(corridorTracks)[0];
    },

    // ── Station Kilometer Mapping Helper ────────────────────────────────────

    getStationKmOnTrack(stationCode, track) {
      if (!track || !stationCode) return null;
      const code = String(stationCode).trim().toUpperCase();

      // 1. Direct match in track.stationKm
      if (track.stationKm && track.stationKm[code] !== undefined) {
        return track.stationKm[code];
      }

      // 2. Direct match in track.stationDetails
      if (track.stationDetails && track.stationDetails[code] !== undefined) {
        return track.stationDetails[code].km;
      }

      // 3. Search by partial code or station name
      if (track.stationDetails) {
        for (const [sCode, details] of Object.entries(track.stationDetails)) {
          if (sCode === code || (details.name && details.name.toUpperCase().includes(code))) {
            return details.km;
          }
        }
      }

      // 4. Match in track.stations array (index corresponds to track.dists)
      if (track.stations && Array.isArray(track.stations)) {
        const idx = track.stations.indexOf(code);
        if (idx >= 0 && track.dists && idx < track.dists.length) {
          return track.dists[idx];
        }
      }

      return null;
    },

    findClosestKmOnTrack(lat, lng, track) {
      if (!track || !track.coords || lat === undefined || lng === undefined) return null;
      let minD = Infinity;
      let bestKm = 0;
      for (let i = 0; i < track.coords.length; i++) {
        const d = this.haversineKm([lat, lng], track.coords[i]);
        if (d < minD) {
          minD = d;
          bestKm = track.dists ? track.dists[i] : 0;
        }
      }
      return bestKm;
    },

    interpolateMissingStationKms(stopsWithKm, totalKm) {
      if (!stopsWithKm || stopsWithKm.length === 0) return;
      if (stopsWithKm[0].resolvedKm === null) {
        stopsWithKm[0].resolvedKm = 0.0;
      }
      if (stopsWithKm[stopsWithKm.length - 1].resolvedKm === null) {
        stopsWithKm[stopsWithKm.length - 1].resolvedKm = totalKm;
      }

      for (let i = 1; i < stopsWithKm.length - 1; i++) {
        if (stopsWithKm[i].resolvedKm === null) {
          let prevIdx = i - 1;
          while (prevIdx >= 0 && stopsWithKm[prevIdx].resolvedKm === null) prevIdx--;
          let nextIdx = i + 1;
          while (nextIdx < stopsWithKm.length && stopsWithKm[nextIdx].resolvedKm === null) nextIdx++;

          const prevKm = stopsWithKm[prevIdx].resolvedKm;
          const nextKm = stopsWithKm[nextIdx].resolvedKm;
          const alpha = (i - prevIdx) / (nextIdx - prevIdx);
          stopsWithKm[i].resolvedKm = prevKm + alpha * (nextKm - prevKm);
        }
      }
    },

    // ── 5. Master Train Position Calculation Algorithm (Station-Anchored) ─────

    calculateTrainPosition(train, nowMin, corridorTracks) {
      const rawStops = train.corridor_stops || [];
      if (rawStops.length < 2) return null;

      // Ensure stops are strictly chronological (True Departure -> Intermediate -> True Destination)
      const stops = this.sortStopsChronologically(rawStops);
      if (stops.length < 2) return null;

      const journeyOrigin = stops[0];
      const journeyDest = stops[stops.length - 1];
      const sFirstCode = (journeyOrigin.station_code || "").toUpperCase();
      const sLastCode = (journeyDest.station_code || "").toUpperCase();

      // 1. Select Track Polyline for this journey
      const track = this.selectCorridorTrack(train, sFirstCode, sLastCode, corridorTracks);
      if (!track || !track.coords || track.coords.length < 2) return null;
      const totalKm = track.totalKm;

      // 2. Resolve exact kilometer position along the polyline track for EVERY fetched station
      const stopsWithKm = stops.map((s, idx) => {
        const code = (s.station_code || "").toUpperCase();
        let km = this.getStationKmOnTrack(code, track);
        if (km === null && s.lat && (s.lng || s.long)) {
          km = this.findClosestKmOnTrack(s.lat, s.lng || s.long, track);
        }
        return {
          ...s,
          station_code: code,
          resolvedKm: km,
          origIndex: idx
        };
      });

      this.interpolateMissingStationKms(stopsWithKm, totalKm);

      // 3. Calculate distance and average speed across ALL fetched stations
      let totalFetchedDistKm = 0;
      let totalFetchedTimeMins = 0;
      for (let j = 0; j < stopsWithKm.length - 1; j++) {
        const j1 = stopsWithKm[j];
        const j2 = stopsWithKm[j + 1];
        const dep = this.parseHHMM(j1.departure || j1.arrival);
        const arr = this.parseHHMM(j2.arrival || j2.departure);
        if (dep !== null && arr !== null) {
          const hop = this.getHopMinutes(dep, arr);
          const dist = Math.abs((j2.resolvedKm ?? 0) - (j1.resolvedKm ?? 0));
          totalFetchedDistKm += dist;
          totalFetchedTimeMins += hop;
        }
      }
      const overallAvgSpeedKmh = totalFetchedTimeMins > 0 ? (totalFetchedDistKm / (totalFetchedTimeMins / 60.0)) : 50.0;

      // 4. Check if train is currently DWELLING / HALTED at an intermediate station halt
      for (let i = 0; i < stopsWithKm.length; i++) {
        const stn = stopsWithKm[i];
        const arr = this.parseHHMM(stn.arrival);
        const dep = this.parseHHMM(stn.departure);
        if (arr !== null && dep !== null && arr !== dep) {
          if (this.isTimeBetween(arr, dep, nowMin)) {
            // Train is halted at this station
            const stnKm = stn.resolvedKm ?? 0;
            const reversed = (stopsWithKm[stopsWithKm.length - 1].resolvedKm < stopsWithKm[0].resolvedKm) ||
                             (sLastCode === "HWH" || sLastCode === "SDAH");
            const offsetLateral = 0.00018 * (reversed ? -1.0 : 1.0);
            const interp = this.interpolateAlongPolyline(track.coords, track.dists, stnKm, offsetLateral);

            return {
              lat: interp.lat,
              lng: interp.lng,
              segIdx: interp.segIdx,
              fraction: 0.0,
              progressPct: Math.round((Math.abs(stnKm - stopsWithKm[0].resolvedKm) / (totalFetchedDistKm || totalKm)) * 100),
              distanceCoveredKm: parseFloat(Math.abs(stnKm - stopsWithKm[0].resolvedKm).toFixed(1)),
              distanceRemainingKm: parseFloat(Math.abs(stopsWithKm[stopsWithKm.length - 1].resolvedKm - stnKm).toFixed(1)),
              totalKm: parseFloat(totalKm.toFixed(1)),
              speedKmh: 0,
              avgSpeedKmh: Math.max(20, Math.min(130, Math.round(overallAvgSpeedKmh))),
              isHalted: true,
              haltStation: stn.station_code,
              haltStationName: stn.station_name || stn.station_code,
              origin: sFirstCode,
              originName: journeyOrigin.station_name || sFirstCode,
              destination: sLastCode,
              destName: journeyDest.station_name || sLastCode,
              finalDest: sLastCode,
              finalDestName: journeyDest.station_name || sLastCode,
              depTime: this.formatHHMM(dep),
              arrTime: this.formatHHMM(arr),
              blockTimeHours: "0.0",
              blockTimeMins: this.getHopMinutes(arr, dep),
              elapsedHours: "0.0",
              elapsedMins: this.getElapsedMinutes(arr, dep, nowMin),
              reversed,
              trackId: track.id,
              trackName: track.name || track.id,
              trainNumber: train.train_number,
              trainName: train.train_name || `Train ${train.train_number}`,
            };
          }
        }
      }

      // 5. Step-by-step segment locator: Find consecutive pair where train is right now
      let activeSeg = null;
      for (let i = 0; i < stopsWithKm.length - 1; i++) {
        const s1 = stopsWithKm[i];
        const s2 = stopsWithKm[i + 1];
        const dep = this.parseHHMM(s1.departure || s1.arrival);
        const arr = this.parseHHMM(s2.arrival || s2.departure);
        if (dep === null || arr === null) continue;

        if (this.isTimeBetween(dep, arr, nowMin)) {
          const elapsed = this.getElapsedMinutes(dep, arr, nowMin);
          const block = this.getHopMinutes(dep, arr);
          if (block > 0) {
            activeSeg = {
              fromStn: s1,
              toStn: s2,
              depMin: dep,
              arrMin: arr,
              elapsedMins: elapsed,
              blockMins: block,
              fraction: Math.min(1.0, Math.max(0.0, elapsed / block)),
              segIndex: i,
            };
            break;
          }
        }
      }

      // If nowMin is outside the journey schedule, train is NOT active
      if (!activeSeg) {
        return null;
      }

      const sFrom = activeSeg.fromStn;
      const sTo = activeSeg.toStn;
      const km1 = sFrom.resolvedKm ?? 0;
      const km2 = sTo.resolvedKm ?? totalKm;

      // Leg distance and section speed:
      const legDistKm = Math.abs(km2 - km1);
      const legBlockHours = activeSeg.blockMins / 60.0;
      const sectionSpeedKmh = legBlockHours > 0 ? (legDistKm / legBlockHours) : overallAvgSpeedKmh;

      // Piece-wise interpolation bounded strictly between station km1 and station km2:
      // At elapsed = 0: exactly at km1 (station sFrom)
      // At elapsed = block: exactly at km2 (station sTo)
      // Train CANNOT cross sTo until arrival time!
      const targetPolyKm = km1 + activeSeg.fraction * (km2 - km1);

      // Direction along polyline:
      const reversed = (km2 < km1) || (sLastCode === "HWH" || sLastCode === "SDAH");
      const offsetLateral = 0.00018 * (reversed ? -1.0 : 1.0);

      const interp = this.interpolateAlongPolyline(track.coords, track.dists, targetPolyKm, offsetLateral);

      const journeyOriginKm = stopsWithKm[0].resolvedKm ?? 0;
      const journeyDestKm = stopsWithKm[stopsWithKm.length - 1].resolvedKm ?? totalKm;
      const distanceCoveredKm = Math.abs(targetPolyKm - journeyOriginKm);
      const distanceRemainingKm = Math.abs(journeyDestKm - targetPolyKm);

      return {
        lat: interp.lat,
        lng: interp.lng,
        segIdx: interp.segIdx,
        fraction: activeSeg.fraction,
        progressPct: Math.round((distanceCoveredKm / (totalFetchedDistKm || totalKm)) * 100),
        distanceCoveredKm: parseFloat(distanceCoveredKm.toFixed(1)),
        distanceRemainingKm: parseFloat(distanceRemainingKm.toFixed(1)),
        totalKm: parseFloat(totalKm.toFixed(1)),
        speedKmh: Math.max(20, Math.min(130, Math.round(sectionSpeedKmh))),
        avgSpeedKmh: Math.max(20, Math.min(130, Math.round(overallAvgSpeedKmh))),
        isHalted: false,
        origin: (sFrom.station_code || "").toUpperCase(),
        originName: sFrom.station_name || sFrom.station_code,
        destination: (sTo.station_code || "").toUpperCase(),
        destName: sTo.station_name || sTo.station_code,
        finalDest: sLastCode,
        finalDestName: journeyDest.station_name || sLastCode,
        depTime: this.formatHHMM(activeSeg.depMin),
        arrTime: this.formatHHMM(activeSeg.arrMin),
        blockTimeHours: (activeSeg.blockMins / 60).toFixed(1),
        blockTimeMins: activeSeg.blockMins,
        elapsedHours: (activeSeg.elapsedMins / 60).toFixed(1),
        elapsedMins: activeSeg.elapsedMins,
        reversed,
        trackId: track.id,
        trackName: track.name || track.id,
        trainNumber: train.train_number,
        trainName: train.train_name || `Train ${train.train_number}`,
      };
    },

    // ── 6. Self-Test / Demonstration Runner ───────────────────────────────────

    testExample() {
      console.log("================================================================");
      console.log("  TrainPathCalculator — Specification Algorithm Verification");
      console.log("================================================================");

      // Create synthetic Sealdah - Krishnanagar line (98.6 km)
      const sampleCoords = [
        [22.568, 88.371], // SDAH (0 km)
        [22.755, 88.375], // Barrackpore (~21 km)
        [22.898, 88.425], // Naihati (~38 km)
        [23.181, 88.568], // Ranaghat (~74 km)
        [23.398, 88.497], // KNJ (~98.6 km)
      ];
      const dists = this.cumulativeDistances(sampleCoords);
      const totalKm = dists[dists.length - 1];

      const sampleTracks = {
        sdah_knj_line: {
          id: "sdah_knj_line",
          name: "Sealdah - Krishnanagar Line",
          coords: sampleCoords,
          dists,
          totalKm,
          stations: ["SDAH", "BP", "NH", "RHA", "KNJ"],
        }
      };

      // Train A: Leaves SDAH at 12:00, reaches KNJ at 16:00, evaluated at 15:00
      const mockTrain = {
        train_number: "31811",
        train_name: "Sealdah - Krishnanagar City Local",
        corridor_id: "sdah_knj_line",
        corridor_stops: [
          { station_code: "SDAH", station_name: "Sealdah", departure: "12:00" },
          { station_code: "KNJ",  station_name: "Krishnanagar City", arrival: "16:00" }
        ]
      };

      const nowMin = this.parseHHMM("15:00"); // 15:00
      const res = this.calculateTrainPosition(mockTrain, nowMin, sampleTracks);

      console.log("Train:", res.trainNumber, "-", res.trainName);
      console.log("Route:", res.origin, `(${res.depTime}) ->`, res.destination, `(${res.arrTime})`);
      console.log("1. Block Time:", res.blockTimeHours, "hours");
      console.log("2. Total Distance along path:", res.totalKm, "km");
      console.log("3. Speed:", res.speedKmh, "km/h");
      console.log("4. Elapsed Time:", res.elapsedHours, "hours");
      console.log("5. Distance from SDAH:", res.distanceFromOriginKm, "km");
      console.log("6. Distance away from KNJ:", res.distanceToDestKm, "km");
      console.log("7. Progress:", res.progressPct + "%");
      console.log("8. Calculated GIS Position:", `[${res.lat.toFixed(6)}, ${res.lng.toFixed(6)}]`);
      console.log("================================================================");
      return res;
    }
  };

  // Expose globally
  global.TrainPathCalculator = TrainPathCalculator;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = TrainPathCalculator;
  }

})(typeof window !== "undefined" ? window : globalThis);

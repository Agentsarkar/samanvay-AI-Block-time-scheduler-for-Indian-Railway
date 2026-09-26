// Timetable Dynamic Generator
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("timetable-container");
  if (!container) return;

  const daySelectorContainer = document.getElementById("timetable-day-selector");
  
  let timetableData = null;
  const days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
  let currentDay = "monday";

  // Fetch the data from our new API
  fetch("/api/timetable-gaps")
    .then(res => res.json())
    .then(data => {
      timetableData = data;
      renderDaySelector();
      renderTimetable(currentDay);
    })
    .catch(err => {
      console.error("Failed to load timetable gaps:", err);
      container.innerHTML = `<div class="p-4 text-red-600 font-bold">Failed to load timetable gaps from server.</div>`;
    });

  function renderDaySelector() {
    if (!daySelectorContainer) return;
    
    let html = `<div class="flex items-center gap-2 text-xs font-semibold">`;
    days.forEach(day => {
      const activeClass = day === currentDay 
        ? "bg-blue-900 text-white border-blue-900" 
        : "bg-white text-slate-700 border-gray-300 hover:bg-gray-100";
      
      html += `
        <button type="button" 
          class="day-btn border px-3 py-1 rounded capitalize transition-colors ${activeClass}" 
          data-day="${day}">
          ${day.substring(0, 3)}
        </button>
      `;
    });
    html += `</div>`;
    
    daySelectorContainer.innerHTML = html;

    // Attach events
    daySelectorContainer.querySelectorAll(".day-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        currentDay = e.target.getAttribute("data-day");
        renderDaySelector();
        renderTimetable(currentDay);
      });
    });
  }

  function renderTimetable(day) {
    if (!timetableData) return;

    const corridors = Object.keys(timetableData);
    if (corridors.length === 0) {
      container.innerHTML = `<div class="p-4 text-gray-500">No corridor data available.</div>`;
      return;
    }

    // Generate Time Axis (24 hours, every 2 hours to save space, or every 1 hour)
    // A 24-hour axis needs to be wide enough. Let's make it min-width: 1200px
    let html = `
      <div class="min-w-[1200px]">
        <div class="grid grid-cols-[120px_repeat(24,1fr)] border-b border-gray-400 pb-1 text-[9px] font-semibold text-gray-700 sticky top-0 bg-white z-20">
          <span class="pl-2">LINE / SECTION</span>
    `;
    for (let h = 0; h < 24; h++) {
      html += `<span>${h.toString().padStart(2, '0')}:00</span>`;
    }
    html += `</div>`;

    // Generate Rows for each Corridor and Direction
    corridors.forEach(cid => {
      ["UP", "DOWN"].forEach(direction => {
        const dayData = timetableData[cid][direction]?.[day];
        if (!dayData || (dayData.gaps.length === 0 && dayData.trains.length === 0)) return;

        const sectionName = `${direction} ${cid.split('_').join(' ').toUpperCase()}`;
        
        html += `
          <div class="grid grid-cols-[120px_1fr] border-b border-gray-300 group hover:bg-gray-50/50">
            <div class="bg-gray-50 px-2 py-3 text-[9px] border-r border-gray-200 flex flex-col justify-center">
              <b class="text-blue-950 leading-tight">${sectionName}</b>
            </div>
            <div class="timeline-grid relative h-16 overflow-hidden bg-gray-50/30">
        `;

        // Render Gaps
        dayData.gaps.forEach(gap => {
          let gStart = gap.gap_start_min;
          let gEnd = gap.gap_end_min;
          if (gStart >= 1440) return;
          if (gEnd > 1440) gEnd = 1440;
          
          const durMin = gEnd - gStart;
          const leftPct = (gStart / 1440) * 100;
          const widthPct = (durMin / 1440) * 100;

          html += `
            <div class="group absolute top-1 bottom-1 bg-green-100/70 border-x border-green-300 flex items-center justify-center overflow-hidden hover:overflow-visible hover:bg-green-200 hover:ring-2 hover:ring-green-400 transition-all z-0 hover:z-30 cursor-crosshair" 
                 style="left:${leftPct}%;width:${widthPct}%"
                 title="Clear Maintenance Window: ${Math.floor(durMin/60)}h ${durMin%60}m">
              <span class="text-green-800 font-bold text-[8px] bg-white/95 px-1 rounded shadow-sm whitespace-nowrap group-hover:scale-125 group-hover:-translate-y-2 transition-transform">
                GAP ${Math.floor(durMin/60)}h ${durMin%60}m
              </span>
            </div>
          `;
        });

        // Render Trains
        // To avoid overlap vertically, we can stack them using modulo
        let highPriorityCount = 0;
        let lowPriorityCount = 0;
        dayData.trains.forEach((train, idx) => {
          let startMin = train.dep_min;
          let endMin = train.arr_min;
          if (startMin >= 1440) return; // Completely next day
          if (endMin > 1440) endMin = 1440; // Cap at midnight

          const leftPct = (startMin / 1440) * 100;
          const widthPct = Math.max(0.5, ((endMin - startMin) / 1440) * 100);
          
          const isHighPriority = train.priority >= 3;

          if (isHighPriority) {
            // High Priority Trains (Large Boxes)
            let bgClass = "bg-blue-800 border-blue-950 text-white";
            if (train.priority === 4) bgClass = "bg-indigo-700 border-indigo-900 text-white"; // Rajdhani/Shatabdi
            
            const topPos = (highPriorityCount % 2 === 0) ? "top-1" : "top-8";
            highPriorityCount++;

            html += `
              <div class="absolute ${topPos} h-5 ${bgClass} border px-1 text-[8px] font-bold leading-[18px] shadow-sm flex items-center gap-1 transition-all overflow-hidden whitespace-nowrap hover:z-20 hover:ring-2 hover:ring-amber-400 cursor-pointer z-10" 
                   style="left:${leftPct}%;width:${widthPct}%"
                   title="${train.train_number} ${train.train_name} (${Math.floor(startMin/60)}:${(startMin%60).toString().padStart(2,'0')} - ${Math.floor(endMin/60)}:${(endMin%60).toString().padStart(2,'0')})">
                <span class="truncate">${train.train_number} ${train.train_name || train.train_type}</span>
              </div>
            `;
          } else {
            // Low Priority Trains (Subtle small boxes)
            let colorClass = train.priority === 1 ? "bg-slate-200 text-slate-600 border-slate-300" : "bg-gray-100 text-gray-500 border-gray-300";
            const topPos = (lowPriorityCount % 2 === 0) ? "top-4" : "bottom-1";
            lowPriorityCount++;
            
            html += `
              <div class="absolute ${topPos} h-3 ${colorClass} border px-1 text-[7px] font-semibold leading-[10px] shadow-sm flex items-center gap-1 transition-all overflow-hidden whitespace-nowrap hover:z-20 hover:ring-2 hover:ring-gray-400 cursor-pointer z-0 opacity-80 hover:opacity-100 hover:h-4" 
                   style="left:${leftPct}%;width:${widthPct}%"
                   title="Low Priority: ${train.train_number} ${train.train_name || train.train_type} (${Math.floor(startMin/60)}:${(startMin%60).toString().padStart(2,'0')} - ${Math.floor(endMin/60)}:${(endMin%60).toString().padStart(2,'0')})">
                <span class="truncate">${train.train_number}</span>
              </div>
            `;
          }
        });

        html += `
            </div>
          </div>
        `;
      });
    });

    html += `</div>`;
    container.innerHTML = html;
  }
});

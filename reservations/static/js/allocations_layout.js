function allocations_layout(allocations) {
    function compareEvents(e1, e2) {
        if (e1.timestamp < e2.timestamp) return -1;
        if (e1.timestamp > e2.timestamp) return 1;
        if (e1.event_type === "end") return -1;
        if (e2.event_type === "end") return 1;
        return 0;
    }
    function firstFreeIndex(integerSet)  {
        for(let i=0; i <= integerSet.size; i++) {
            if (!integerSet.has(i)) {
                return i;
            }
        }
        return -1;
    }
    let runningAllocations = new Set();
    let takenIndices = new Set();
    let events =
        [for (a of allocations) {"event_type": "start",
            "timestamp": a.start,
            "allocation": a
        }].concat(
        [for (a of allocations)
        {"event_type": "end",
            "timestamp": a.end,
            "allocation": a
        }]);
    events.sort(compareEvents);
    for (let event of events) {
        if (event.event_type === "start") {
            let index = firstFreeIndex(takenIndices);
            runningAllocations.add(event.allocation);
            takenIndices.add(index);
            event.allocation.index = event.allocation.max_index = index;
        }
        else {
            runningAllocations.delete(event.allocation);
            takenIndices.delete(event.allocation.index);
        }
        for(let runningAllocation of runningAllocations) {
            event.allocation.max_index = Math.max(runningAllocation.max_index, event.allocation.index);
        }
    }
    return allocations;
}


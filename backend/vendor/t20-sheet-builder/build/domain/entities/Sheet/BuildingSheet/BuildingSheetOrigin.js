"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BuildingSheetOrigin = void 0;
class BuildingSheetOrigin {
    constructor(origin = undefined) {
        this.origin = origin;
    }
    chooseOrigin(origin, transaction) {
        this.origin = origin;
        this.origin.addToSheet(transaction);
    }
    getOrigin() {
        return this.origin;
    }
}
exports.BuildingSheetOrigin = BuildingSheetOrigin;

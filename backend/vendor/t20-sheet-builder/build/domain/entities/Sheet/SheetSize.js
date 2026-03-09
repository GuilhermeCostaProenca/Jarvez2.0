"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetSize = void 0;
const Size_1 = require("../Size/Size");
const SizeName_1 = require("../Size/SizeName");
class SheetSize {
    constructor(size = Size_1.sizes[SizeName_1.SizeName.medium]) {
        this.size = size;
    }
    changeSize(size) {
        this.size = size;
    }
    getSize() {
        return this.size.name;
    }
    getOccupiedSpaceInMeters() {
        return this.size.occupiedSpaceInMeters;
    }
    getManeuversModifier() {
        return this.size.maneuversModifier;
    }
    getFurtivityModifier() {
        return this.size.furtivityModifier;
    }
}
exports.SheetSize = SheetSize;

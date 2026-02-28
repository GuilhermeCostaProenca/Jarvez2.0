"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetVision = void 0;
const Vision_1 = require("./Vision");
class SheetVision {
    constructor(vision = Vision_1.Vision.default) {
        this.vision = vision;
    }
    changeVision(vision) {
        this.vision = vision;
    }
    getVision() {
        return this.vision;
    }
}
exports.SheetVision = SheetVision;

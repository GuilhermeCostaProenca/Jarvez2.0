"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetDisplacement = void 0;
const errors_1 = require("../../errors");
class SheetDisplacement {
    constructor(displacement = 9) {
        this.displacement = displacement;
        this.climbingDisplacement = undefined;
    }
    changeDisplacement(displacement) {
        if (displacement < 0) {
            throw new errors_1.SheetBuilderError('DISPLACEMENT_CANNOT_BE_NEGATIVE');
        }
        this.displacement = displacement;
    }
    changeClimbingDisplacement(climbingDisplacement) {
        if (climbingDisplacement < 0) {
            throw new errors_1.SheetBuilderError('CLIMBING_DISPLACEMENT_CANNOT_BE_NEGATIVE');
        }
        this.climbingDisplacement = climbingDisplacement;
    }
    getDisplacement() {
        return this.displacement;
    }
    getClimbingDisplacement() {
        return this.climbingDisplacement;
    }
}
exports.SheetDisplacement = SheetDisplacement;

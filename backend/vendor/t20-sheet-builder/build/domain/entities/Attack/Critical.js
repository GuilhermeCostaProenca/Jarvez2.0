"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Critical = void 0;
const SheetBuilderError_1 = require("../../errors/SheetBuilderError");
class Critical {
    constructor(threat = 20, multiplier = 2) {
        this.threat = threat;
        this.multiplier = multiplier;
        this.validateThreat(threat);
        this.validateMultiplier(multiplier);
    }
    serialize() {
        return {
            threat: this.threat,
            multiplier: this.multiplier,
        };
    }
    validateThreat(threat) {
        if (threat < 0) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_NEGATIVE_THREAT');
        }
        if (threat > 20) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_MAX_THREAT_EXCEEDED');
        }
    }
    validateMultiplier(multiplier) {
        if (multiplier < 2) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_MIN_MULTIPLIER');
        }
    }
}
exports.Critical = Critical;

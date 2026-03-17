"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProgressionStepFake = void 0;
class ProgressionStepFake {
    constructor(action) {
        this.action = action;
        this.description = action.type;
    }
    serialize() {
        return {
            action: {
                type: this.action.type,
                description: this.action.description,
            },
        };
    }
}
exports.ProgressionStepFake = ProgressionStepFake;

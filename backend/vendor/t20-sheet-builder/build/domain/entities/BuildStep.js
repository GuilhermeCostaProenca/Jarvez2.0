"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BuildStep = void 0;
class BuildStep {
    constructor(action) {
        this.action = action;
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
exports.BuildStep = BuildStep;

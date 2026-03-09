"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TemporaryModifier = void 0;
const Modifier_1 = require("../Modifier");
class TemporaryModifier extends Modifier_1.Modifier {
    constructor(source, value, duration) {
        super({
            source,
            type: 'temporary',
            value,
        });
        this.duration = duration;
    }
}
exports.TemporaryModifier = TemporaryModifier;

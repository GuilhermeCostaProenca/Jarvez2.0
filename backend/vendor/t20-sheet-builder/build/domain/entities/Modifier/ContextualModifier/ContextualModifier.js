"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContextualModifier = void 0;
const Modifier_1 = require("../Modifier");
class ContextualModifier extends Modifier_1.Modifier {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'contextual' }));
        this.condition = params.condition;
    }
}
exports.ContextualModifier = ContextualModifier;

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EffectAffectableTarget = exports.EffectAffectableArea = exports.EffectAffectable = void 0;
const SheetBuilderError_1 = require("../../errors/SheetBuilderError");
class EffectAffectable {
    constructor(affectableType) {
        this.affectableType = affectableType;
    }
}
exports.EffectAffectable = EffectAffectable;
class EffectAffectableArea extends EffectAffectable {
    constructor(format) {
        super('area');
        this.format = format;
    }
}
exports.EffectAffectableArea = EffectAffectableArea;
class EffectAffectableTarget extends EffectAffectable {
    constructor(targetType, quantity) {
        super('target');
        this.targetType = targetType;
        this.quantity = quantity;
        if (quantity <= 0) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_TARGET_QUANTITY');
        }
    }
}
exports.EffectAffectableTarget = EffectAffectableTarget;

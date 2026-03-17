"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AffectableTargetCreature = exports.AffectableTarget = void 0;
class AffectableTarget {
    get affectableType() {
        return 'target';
    }
    constructor(targetType) {
        this.targetType = targetType;
    }
}
exports.AffectableTarget = AffectableTarget;
class AffectableTargetCreature extends AffectableTarget {
    constructor() {
        super('creature');
    }
}
exports.AffectableTargetCreature = AffectableTargetCreature;

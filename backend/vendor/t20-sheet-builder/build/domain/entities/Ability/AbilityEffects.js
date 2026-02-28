"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AbilityEffects = void 0;
class AbilityEffects {
    constructor(params) {
        var _a, _b, _c, _d;
        this.passive = (_a = params === null || params === void 0 ? void 0 : params.passive) !== null && _a !== void 0 ? _a : {};
        this.triggered = (_b = params === null || params === void 0 ? void 0 : params.triggered) !== null && _b !== void 0 ? _b : {};
        this.activateable = (_c = params === null || params === void 0 ? void 0 : params.activateable) !== null && _c !== void 0 ? _c : {};
        this.roleplay = (_d = params === null || params === void 0 ? void 0 : params.roleplay) !== null && _d !== void 0 ? _d : {};
    }
    serialize() {
        const effects = {
            passive: Object.values(this.passive),
            triggered: Object.values(this.triggered),
            activateable: Object.values(this.activateable),
            roleplay: Object.values(this.roleplay),
        };
        return Object.values(effects).flat().map(effect => effect.serialize());
    }
}
exports.AbilityEffects = AbilityEffects;

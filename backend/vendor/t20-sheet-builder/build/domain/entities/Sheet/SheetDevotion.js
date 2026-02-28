"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetDevotion = void 0;
class SheetDevotion {
    constructor() {
        this.devotion = undefined;
        this.grantedPowerCount = 1;
    }
    isDevout() {
        return Boolean(this.devotion);
    }
    becomeDevout(devotion, transaction) {
        this.devotion = devotion;
        devotion.addToSheet(transaction);
    }
    getGrantedPowerCount() {
        return this.grantedPowerCount;
    }
    changeGrantedPowerCount(count) {
        this.grantedPowerCount = count;
    }
    getDeity() {
        var _a;
        return (_a = this.devotion) === null || _a === void 0 ? void 0 : _a.deity;
    }
    addGrantedPower(power) {
        var _a;
        (_a = this.devotion) === null || _a === void 0 ? void 0 : _a.addPower(power);
    }
    removeGrantedPower(powerName) {
        var _a;
        (_a = this.devotion) === null || _a === void 0 ? void 0 : _a.removePower(powerName);
    }
    serialize() {
        var _a;
        return {
            devotion: (_a = this.devotion) === null || _a === void 0 ? void 0 : _a.serialize(),
            grantedPowerCount: this.grantedPowerCount,
        };
    }
}
exports.SheetDevotion = SheetDevotion;

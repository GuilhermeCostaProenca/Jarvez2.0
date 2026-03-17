"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WeaponPurposeRangedShooting = void 0;
const WeaponPurposeRanged_1 = require("./WeaponPurposeRanged");
class WeaponPurposeRangedShooting extends WeaponPurposeRanged_1.WeaponPurposeRanged {
    constructor(params = {}) {
        var _a;
        super(Object.assign(Object.assign({}, params), { damageAttribute: (_a = params.damageAttribute) !== null && _a !== void 0 ? _a : undefined }));
    }
}
exports.WeaponPurposeRangedShooting = WeaponPurposeRangedShooting;

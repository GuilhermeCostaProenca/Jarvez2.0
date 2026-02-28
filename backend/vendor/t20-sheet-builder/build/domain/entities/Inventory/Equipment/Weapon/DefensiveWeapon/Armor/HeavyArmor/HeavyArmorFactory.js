"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HeavyArmorFactory = void 0;
const HeavyArmors_1 = require("./HeavyArmors");
class HeavyArmorFactory {
    static make(name) {
        return new (HeavyArmors_1.HeavyArmors.get(name))();
    }
}
exports.HeavyArmorFactory = HeavyArmorFactory;

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LightArmorFactory = void 0;
const LightArmors_1 = require("./LightArmors");
class LightArmorFactory {
    static make(name) {
        return new (LightArmors_1.LightArmors.get(name))();
    }
}
exports.LightArmorFactory = LightArmorFactory;

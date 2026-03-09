"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Armors = void 0;
const HeavyArmor_1 = require("./HeavyArmor");
const LightArmor_1 = require("./LightArmor");
class Armors {
    static get(name) {
        return Armors.map[name];
    }
    static getAll() {
        return Object.values(Armors.map);
    }
}
exports.Armors = Armors;
Armors.map = Object.assign(Object.assign({}, LightArmor_1.LightArmors.map), HeavyArmor_1.HeavyArmors.map);

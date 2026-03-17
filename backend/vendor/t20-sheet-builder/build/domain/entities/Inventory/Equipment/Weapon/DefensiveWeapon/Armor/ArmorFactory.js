"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArmorFactory = void 0;
const Armors_1 = require("./Armors");
class ArmorFactory {
    static make(name) {
        return new (Armors_1.Armors.get(name))();
    }
}
exports.ArmorFactory = ArmorFactory;

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathSerializerMage = void 0;
const ArcanistPathSerializer_1 = require("./ArcanistPathSerializer");
class ArcanistPathSerializerMage extends ArcanistPathSerializer_1.ArcanistPathSerializer {
    constructor(path) {
        super();
        this.path = path;
    }
    serialize() {
        return {
            extraSpell: this.path.getExtraSpell().name,
            name: this.path.pathName,
        };
    }
}
exports.ArcanistPathSerializerMage = ArcanistPathSerializerMage;

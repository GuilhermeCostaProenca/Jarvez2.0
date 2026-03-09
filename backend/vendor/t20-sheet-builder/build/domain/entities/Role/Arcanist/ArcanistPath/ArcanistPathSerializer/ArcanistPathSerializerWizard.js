"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathSerializerWizard = void 0;
const ArcanistPathSerializer_1 = require("./ArcanistPathSerializer");
class ArcanistPathSerializerWizard extends ArcanistPathSerializer_1.ArcanistPathSerializer {
    constructor(path) {
        super();
        this.path = path;
    }
    serialize() {
        return {
            focus: this.path.getFocus().equipment.name,
            name: this.path.pathName,
        };
    }
}
exports.ArcanistPathSerializerWizard = ArcanistPathSerializerWizard;

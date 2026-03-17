"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetSerializer = void 0;
/**
* @deprecated Use `sheet.serialize()` instead
*/
class SheetSerializer {
    constructor(context) {
        this.context = context;
    }
    serialize(sheet) {
        return sheet.serialize(this.context);
    }
}
exports.SheetSerializer = SheetSerializer;

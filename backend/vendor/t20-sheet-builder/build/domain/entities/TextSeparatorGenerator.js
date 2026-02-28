"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TextSeparatorGenerator = void 0;
class TextSeparatorGenerator {
    static generateSeparator(index, arrayLength) {
        const isNotLast = index !== arrayLength - 1;
        const isNextLast = index + 1 === arrayLength - 1;
        const separator = isNextLast
            ? ' e '
            : isNotLast
                ? ', '
                : '';
        return separator;
    }
}
exports.TextSeparatorGenerator = TextSeparatorGenerator;

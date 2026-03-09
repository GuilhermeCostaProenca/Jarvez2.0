import type { Attributes } from '../Sheet/Attributes';
import { type RaceAbility } from './RaceAbility';
import type { RaceInterface } from './RaceInterface';
import { RaceName } from './RaceName';
export declare class RaceFake implements RaceInterface {
    serialize: import("vitest").Mock<any, any>;
    abilities: Record<string, RaceAbility>;
    name: RaceName;
    attributeModifiers: Partial<Attributes>;
    applyAbilities: import("vitest").Mock<any, any>;
    applyAttributesModifiers: import("vitest").Mock<[attributes: Attributes], Attributes>;
    addToSheet: import("vitest").Mock<any, any>;
}

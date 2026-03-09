import { type Character } from '../../../../Character';
import { FightStyleEffect } from './FightStyleEffect';
export declare class OneWeaponStyleEffect extends FightStyleEffect {
    static description: string;
    get description(): string;
    constructor();
    canApply(character: Character): boolean;
}

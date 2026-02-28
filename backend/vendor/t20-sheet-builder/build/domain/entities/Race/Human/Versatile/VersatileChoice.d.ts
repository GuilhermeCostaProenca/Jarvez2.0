import { type GeneralPowerName } from '../../../Power';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
import { type SkillName } from '../../../Skill';
import type { TranslatableName } from '../../../Translator';
import { type SerializedVersatileChoice } from '../../SerializedRace';
export type VersatileChoiceType = 'skill' | 'power';
export declare abstract class VersatileChoice {
    readonly name: SkillName | GeneralPowerName;
    readonly type: VersatileChoiceType;
    constructor(name: SkillName | GeneralPowerName, type: VersatileChoiceType);
    abstract addToSheet(transaction: TransactionInterface, source: TranslatableName): void;
    abstract serialize(): SerializedVersatileChoice;
}

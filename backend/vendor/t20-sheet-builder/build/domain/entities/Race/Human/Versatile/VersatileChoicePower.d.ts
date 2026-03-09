import { type GeneralPowerName } from '../../../Power';
import type { GeneralPowerInterface } from '../../../Power/GeneralPower/GeneralPower';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
import type { TranslatableName } from '../../../Translator';
import { type SerializedVersatileChoicePower } from '../../SerializedRace';
import { VersatileChoice } from './VersatileChoice';
export declare class VersatileChoicePower extends VersatileChoice {
    readonly power: GeneralPowerInterface;
    readonly name: GeneralPowerName;
    constructor(power: GeneralPowerInterface);
    addToSheet(transaction: TransactionInterface, source: TranslatableName): void;
    serialize(): SerializedVersatileChoicePower;
}

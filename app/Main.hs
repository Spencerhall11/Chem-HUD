{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE DeriveGeneric #-}

module Main where

import qualified Data.Map as Map
import qualified Data.ByteString.Lazy as BL
import Data.Csv hiding (Parser)
import qualified Data.Vector as V
import GHC.Generics (Generic)
import System.Exit (die)
import Text.Read (readMaybe)
import Text.Parsec
import Text.Parsec.String (Parser)
import Control.Monad (forever)

-- | Data structure for an Element
data Atom = Atom
  { symbol          :: String
  , name            :: String
  , weight          :: Double  -- Changed to Double for direct math
  , elementCategory :: String
  , meltingPoint    :: String
  , boilingPoint    :: String
  , electroneg      :: String
  } deriving (Show, Generic)

-- | Recursive data types for Molecules
type Molecule = [FormulaComponent]

data FormulaComponent
    = SingleAtom Atom Int           -- e.g., H2
    | SubMolecule Molecule Int      -- e.g., (OH)2
    deriving (Show)

-- | CSV Parsing Logic
instance FromNamedRecord Atom where
    parseNamedRecord r = Atom 
        <$> r .: "Symbol" 
        <*> r .: "Element" 
        -- Safely convert the Mass string to a Double
        <*> (fmap (maybe 0.0 id . readMaybe) (r .: "AtomicMass"))
        <*> r .: "Type"
        <*> r .: "MeltingPoint"
        <*> r .: "BoilingPoint"
        <*> r .: "Electronegativity"

-- | Load the Periodic Table into a Map for O(1) lookup
loadElements :: IO (Map.Map String Atom)
loadElements = do
    csvData <- BL.readFile "Periodic Table of Elements.csv"
    case decodeByName csvData of
        Left err -> die $ "Failed to parse CSV: " ++ err
        Right (_, v) -> return $ Map.fromList 
                               $ V.toList 
                               $ V.map (\a -> (symbol a, a)) v

-- | Recursive Math: Summing the mass of the entire structure
calculateTotalMass :: Molecule -> Double
calculateTotalMass components = sum $ map componentMass components
  where
    componentMass (SingleAtom a count)    = weight a * fromIntegral count
    componentMass (SubMolecule mol count) = calculateTotalMass mol * fromIntegral count

-------------------------------------------------------------------------------
-- RECURSIVE DESCENT PARSER
-- This turns "Mg(OH)2" into [SingleAtom Mg 1, SubMolecule [O1, H1] 2]
-------------------------------------------------------------------------------

moleculeParser :: Map.Map String Atom -> Parser Molecule
moleculeParser elements = many1 (componentParser elements)

componentParser :: Map.Map String Atom -> Parser FormulaComponent
componentParser elements = subMolecule <|> singleAtom
  where
    -- Handles bracketed groups: (OH)2
    subMolecule = do
        _ <- char '('
        sub <- many1 (componentParser elements)
        _ <- char ')'
        count <- option 1 (read <$> many1 digit)
        return $ SubMolecule sub count

    -- Handles atoms: Mg or H2
    singleAtom = do
        sym <- symbolParser
        count <- option 1 (read <$> many1 digit)
        case Map.lookup sym elements of
            Just a  -> return $ SingleAtom a count
            Nothing -> fail $ "Unknown element: " ++ sym

    -- Elements are Uppercase followed by optional lowercase (He, Li, O)
    symbolParser = (:) <$> upper <*> many lower

-------------------------------------------------------------------------------
-- MAIN EXECUTION LOOP
-------------------------------------------------------------------------------

main :: IO ()
main = do 
    elements <- loadElements
    putStrLn "--- ChemHUD Brain Active ---"
    putStrLn "Ready for input from Python Eye..."

    -- 'forever' keeps the process alive to handle strings via the Nerve pipe
    forever $ do
        line <- getLine
        if null line 
          then return () 
          else case parse (moleculeParser elements) "" line of
            Left err -> putStrLn $ "Error parsing '" ++ line ++ "': " ++ show err
            Right mol -> do
                let totalMass = calculateTotalMass mol
                putStrLn $ ">> Analyzed: " ++ line
                putStrLn $ ">> Total Molecular Mass: " ++ show totalMass ++ " u"
                putStrLn "----------------------------"
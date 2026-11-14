// Power Query: create a blank query named FactFlight; paste in Advanced Editor.
// Change only ProjectRoot for your machine. The source is a single gzip CSV.
let
    ProjectRoot = "C:\path\to\flight-delay-operations-analytics",
    Binary = Binary.Decompress(File.Contents(ProjectRoot & "\data\processed\flights_cleaned.csv.gz"), Compression.GZip),
    CSV = Csv.Document(Binary, [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(CSV, [PromoteAllScalars=true]),
    EmptyToNull = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
    TextColumns = {"AIRLINE", "TAIL_NUMBER", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT", "CANCELLATION_REASON", "TIME_BAND", "SEASON", "ORIGIN_KEY", "DESTINATION_KEY", "ROUTE"},
    NumericColumns = List.Difference(Table.ColumnNames(EmptyToNull), List.Combine({TextColumns, {"DATE"}})),
    NumericTypes = List.Transform(NumericColumns, each {_, Int64.Type}),
    TextTypes = List.Transform(TextColumns, each {_, type text}),
    Typed = Table.TransformColumnTypes(EmptyToNull, List.Combine({NumericTypes, TextTypes, {{"DATE", type date}}}), "en-US")
in
    Typed
